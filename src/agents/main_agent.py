"""
主Agent - 使用 LangChain Agent
负责理解用户意图，调用工具，生成旅游规划
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.utils.function_calling import convert_to_openai_function

# 默认导入所有工具
from src.skills import get_all_tools


class MainAgent:
    """主Agent：使用 LangChain 架构"""

    def __init__(self, llm: ChatOpenAI, tools: list = None):
        self.llm = llm
        # 如果没有传入 tools，默认获取所有工具
        self.tools = tools if tools is not None else get_all_tools()
        self._setup_functions()

    def _setup_functions(self):
        """设置可用的函数"""
        # 将 tools 转换为函数定义
        if self.tools:
            self.functions = [convert_to_openai_function(tool) for tool in self.tools]
            self.llm_with_tools = self.llm.bind(functions=self.functions)
        else:
            self.functions = []
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
            response = self.llm_with_tools.invoke(messages)

            # 检查是否有函数调用
            if hasattr(response, "additional_kwargs") and response.additional_kwargs.get("function_call"):
                # 处理函数调用
                function_call = response.additional_kwargs["function_call"]
                function_name = function_call["name"]
                arguments = function_call["arguments"]

                # 获取工具并执行
                tool = self._get_tool(function_name)
                if tool:
                    result = tool.invoke(arguments)
                    # 再次调用 LLM 处理结果
                    messages.append(response)
                    messages.append(HumanMessage(content=f"工具 {function_name} 返回结果: {result}"))
                    final_response = self.llm.invoke(messages)
                    return final_response.content
                else:
                    return f"未找到工具: {function_name}"
            else:
                return response.content
        except Exception as e:
            return f"处理过程中出现错误：{str(e)}"

    def _get_tool(self, tool_name: str):
        """根据名称获取工具"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
