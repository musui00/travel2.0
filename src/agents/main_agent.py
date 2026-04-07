"""
主Agent - 使用 LangChain Agent
负责理解用户意图，调用工具，生成旅游规划
"""

import json
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 默认导入所有工具
from src.skills import get_all_tools

# 重试配置
MAX_RETRIES = 3


class ToolInvokeError(Exception):
    """工具调用错误"""

    def __init__(self, error_message: str, tool_name: str = ""):
        self.error_message = error_message
        self.tool_name = tool_name
        super().__init__(error_message)


class MainAgent:
    """主Agent：使用 LangChain 架构"""

    def __init__(self, llm: ChatOpenAI, tools: list = None):
        self.llm = llm
        # 如果没有传入 tools，默认获取所有工具
        self.tools = tools if tools is not None else get_all_tools()
        self._setup_functions()

    def _setup_functions(self):
        """设置可用的函数"""
        # FIX: 使用 bind_tools 而非 bind(functions=...)
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

    def run(self, user_input: str, image_analysis: str = "") -> str:
        """
        主Agent执行入口

        Args:
            user_input: 用户输入
            image_analysis: 图片分析结果

        Returns:
            完整的旅游规划
        """
        print("=" * 60)
        print("【LangChain Agent】开始处理...")
        print("=" * 60)

        # 构建输入
        if image_analysis:
            input_text = f"图片分析结果：{image_analysis}\n\n用户需求：{user_input}"
        else:
            input_text = user_input

        # 执行 LLM
        try:
            messages = [HumanMessage(content=input_text)]
            return self._run_with_retry(messages)
        except Exception as e:
            return f"处理过程中出现错误：{str(e)}"

    def _run_with_retry(self, messages: list, retry_count: int = 0) -> str:
        """
        三层重试机制执行

        Args:
            messages: 消息列表
            retry_count: 当前重试次数

        Returns:
            最终响应内容
        """
        try:
            response = self.llm_with_tools.invoke(messages)

            # 检查是否有函数调用（LangChain 0.3+ 使用 tool_calls）
            function_call = None
            if hasattr(response, "tool_calls") and response.tool_calls:
                tc = response.tool_calls[0]
                tool_name = getattr(tc, "name", None) or tc.get("name")
                if tool_name:
                    tool_args = getattr(tc, "args", None) or tc.get("args", {})
                    if isinstance(tool_args, str):
                        arguments = tool_args
                    else:
                        arguments = json.dumps(tool_args)
                    function_call = {"name": tool_name, "arguments": arguments}
            elif hasattr(
                response, "additional_kwargs"
            ) and response.additional_kwargs.get("function_call"):
                function_call = response.additional_kwargs["function_call"]

            if function_call:
                function_name = function_call["name"]
                arguments = function_call["arguments"]

                # 获取工具并执行（带重试）
                tool = self._get_tool(function_name)
                if tool:
                    return self._invoke_tool_with_retry(
                        tool, arguments, function_name, messages, response, retry_count
                    )
                else:
                    return f"未找到工具: {function_name}"
            else:
                return response.content
        except Exception as e:
            return f"处理过程中出现错误：{str(e)}"

    def _invoke_tool_with_retry(
        self,
        tool: Any,
        arguments: str,
        function_name: str,
        messages: list,
        response: Any,
        retry_count: int,
    ) -> str:
        """
        工具调用三层重试

        Layer 1: 基础重试 - 工具调用失败时重试
        Layer 2: 参数修正 - 参数错误时重新生成参数
        Layer 3: 替代工具 - API不可用时尝试其他工具
        """
        try:
            # 解析参数
            args = json.loads(arguments) if isinstance(arguments, str) else arguments
            result = tool.invoke(args)
            return self._process_tool_result(
                tool, result, function_name, messages, response
            )
        except ToolInvokeError as e:
            # Layer 1: 基础重试 - 重新调用工具
            if retry_count < MAX_RETRIES:
                print(
                    f"⚠️ 工具 {function_name} 调用失败，进行第 {retry_count + 1} 次重试..."
                )
                return self._run_with_retry(messages, retry_count + 1)

            # Layer 2: 参数错误修正
            return self._error_correction(
                e, function_name, messages, response, retry_count
            )
        except Exception as e:
            error_msg = str(e)
            # 判断错误类型
            if "参数" in error_msg or "invalid" in error_msg.lower():
                # 参数错误 - 尝试修正参数
                return self._correct_parameters(
                    error_msg, function_name, messages, response, retry_count
                )
            elif "API" in error_msg or "timeout" in error_msg.lower():
                # API不可用 - 尝试替代工具
                return self._try_alternative_tool(
                    error_msg, function_name, messages, response
                )
            else:
                # 业务错误（如无结果）- 直接返回合理回复
                return self._handle_business_error(
                    error_msg, function_name, messages, response
                )

    def _error_correction(
        self,
        e: ToolInvokeError,
        function_name: str,
        messages: list,
        response: Any,
        retry_count: int,
    ) -> str:
        """
        错误修正 Prompt - Layer 2 & 3
        """
        correction_prompt = f"""
上一次工具调用失败，错误原因：{e.error_message}

请判断：
1. 如果是参数错误（如缺少必填参数、参数格式不对），重新生成正确的参数
2. 如果是 API 不可用（超时、服务不可用），尝试调用其他工具实现相同功能
3. 如果是业务错误（如查询无结果），直接返回合理回复，不再次调用工具
"""
        messages = messages + [response, HumanMessage(content=correction_prompt)]

        # 再次调用 LLM
        correction_response = self.llm.invoke(messages)

        # 检查是否有新的函数调用（LangChain 0.3+ 使用 tool_calls）
        new_function_call = None
        if (
            hasattr(correction_response, "tool_calls")
            and correction_response.tool_calls
        ):
            for tc in correction_response.tool_calls:
                if tc.get("name"):
                    new_function_call = {
                        "name": tc["name"],
                        "arguments": tc.get("args", "{}"),
                    }
                    break
        elif hasattr(
            correction_response, "additional_kwargs"
        ) and correction_response.additional_kwargs.get("function_call"):
            new_function_call = correction_response.additional_kwargs["function_call"]

        if new_function_call:
            new_function_name = new_function_call["name"]
            new_arguments = new_function_call["arguments"]

            messages.append(correction_response)
            return self._invoke_tool_with_retry(
                self._get_tool(new_function_name),
                new_arguments,
                new_function_name,
                messages,
                correction_response,
                retry_count + 1,
            )
        else:
            return correction_response.content

    def _correct_parameters(
        self,
        error_msg: str,
        function_name: str,
        messages: list,
        response: Any,
        retry_count: int,
    ) -> str:
        """Layer 2: 参数修正"""
        param_fix_prompt = f"""
工具 {function_name} 调用失败，错误原因：{error_msg}

请重新生成正确的参数，确保：
1. 所有必填参数都已提供
2. 参数格式正确��如日期格式、编号格式等）
3. 参数值在有效范围内
"""
        messages = messages + [response, HumanMessage(content=param_fix_prompt)]
        correction_response = self.llm.invoke(messages)

        # 检查是否有函数调用（LangChain 0.3+ 使用 tool_calls）
        new_function_call = None
        if (
            hasattr(correction_response, "tool_calls")
            and correction_response.tool_calls
        ):
            for tc in correction_response.tool_calls:
                if tc.get("name"):
                    new_function_call = {
                        "name": tc["name"],
                        "arguments": tc.get("args", "{}"),
                    }
                    break
        elif hasattr(
            correction_response, "additional_kwargs"
        ) and correction_response.additional_kwargs.get("function_call"):
            new_function_call = correction_response.additional_kwargs["function_call"]

        if new_function_call:
            new_function_name = new_function_call["name"]
            new_arguments = new_function_call["arguments"]

            tool = self._get_tool(new_function_name)
            return self._invoke_tool_with_retry(
                tool,
                new_arguments,
                new_function_name,
                messages + [correction_response],
                correction_response,
                retry_count + 1,
            )
        return correction_response.content

    def _try_alternative_tool(
        self,
        error_msg: str,
        function_name: str,
        messages: list,
        response: Any,
    ) -> str:
        """Layer 3: 尝试替代工具"""
        alt_prompt = f"""
工具 {function_name} 不可用（{error_msg}）

请尝试调用其他工具实现相同功能，或直接返回当前可用的信息。
"""
        messages = messages + [response, HumanMessage(content=alt_prompt)]
        alt_response = self.llm.invoke(messages)
        return alt_response.content

    def _handle_business_error(
        self,
        error_msg: str,
        function_name: str,
        messages: list,
        response: Any,
    ) -> str:
        """处理业务错误（如查询无结果）"""
        business_prompt = f"""
工具 {function_name} 返回：{error_msg}

请直接返回合理回复，不需要再次调用工具。
"""
        messages = messages + [response, HumanMessage(content=business_prompt)]
        return self.llm.invoke(messages).content

    def _process_tool_result(
        self,
        tool: Any,
        result: str,
        function_name: str,
        messages: list,
        response: Any,
    ) -> str:
        """处理工具结果并生成最终响应"""
        messages.append(response)
        messages.append(
            HumanMessage(content=f"工具 {function_name} 返回结果: {result}")
        )
        final_response = self.llm.invoke(messages)
        return final_response.content

    def _get_tool(self, tool_name: str):
        """根据名称获取工具"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
