"""
住宿领域 Sub-Agent
负责处理酒店、民宿推荐
"""

import json
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# 导入住宿领域 Tools
from src.skills import recommend_hotel, recommend_bnb


class AccommodationAgent:
    """住宿领域 Agent - 处理酒店和民宿推荐"""

    def __init__(self, llm: Any):
        """初始化 Accommodation Agent

        Args:
            llm: LangChain LLM 实例
        """
        self.llm = llm
        self.tools = [recommend_hotel, recommend_bnb]
        self._setup_tools()

    def _setup_tools(self) -> None:
        """绑定 Tools 到 LLM"""
        if self.tools:
            # FIX: 使用 bind_tools 而非 bind(functions=...)
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的住宿顾问。

## 你的专长：
1. 酒店推荐：根据预算推荐豪华/舒适/经济型酒店
2. 民宿推荐：推荐特色民宿

## 你可以使用的工具：
- recommend_hotel：推荐酒店
- recommend_bnb：推荐民宿

## 输出要求：
请根据用户需求（目标城市、预算偏好）调用合适的工具，然后基于工具返回结果给出住宿建议。
请用中文回复。"""

    def invoke(self, state: dict) -> dict:
        """执行住宿任务，调用工具并更新状态

        Args:
            state: 包含 messages 和 travel_plan 的状态字典

        Returns:
            更新后的状态字典
        """
        messages = state.get("messages", [])
        travel_plan = state.get("travel_plan", {})

        # FIX: BUG-3 只传递必要上下文
        user_input = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_input = msg.content
                break

        # 构建精简消息列表
        full_messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=user_input),
        ]

        # 添加已收集的关键信息
        if travel_plan:
            key_info = "已收集的关键信息：\n"
            for key, value in travel_plan.items():
                if value:
                    key_info += f"- {key}: 已收集\n"
            full_messages.append(HumanMessage(content=key_info))

        try:
            response = self.llm_with_tools.invoke(full_messages)

            # 检查是否有函数调用（LangChain 0.3+ 使用 tool_calls）
            function_call = None
            if hasattr(response, "tool_calls") and response.tool_calls:
                tc = response.tool_calls[0]
                tool_name = getattr(tc, "name", None) or tc.get("name")
                if tool_name:
                    tool_args = getattr(tc, "args", None) or tc.get("args", {})
                    if isinstance(tool_args, dict):
                        arguments = json.dumps(tool_args)
                    else:
                        arguments = tool_args
                    function_call = {"name": tool_name, "arguments": arguments}
            elif hasattr(
                response, "additional_kwargs"
            ) and response.additional_kwargs.get("function_call"):
                function_call = response.additional_kwargs["function_call"]

            if function_call:
                tool_name = function_call.get("name", "")
                arguments = function_call.get("arguments", "{}")

                try:
                    tool_args = json.loads(arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                tool = self._get_tool(tool_name)
                if tool:
                    try:
                        tool_result = tool.invoke(tool_args)
                    except Exception as tool_err:
                        tool_result = f"工具执行失败: {str(tool_err)}"
                        logger.error(f"[AccommodationAgent] 工具执行失败: {tool_err}")

                    # FIX-1: 防御性检查 - 如果 LLM 返回为空，使用原始工具结果
                    try:
                        final_response = self.llm.invoke(result_messages)
                        if not final_response or not getattr(
                            final_response, "content", None
                        ):
                            final_content = tool_result
                            logger.warning(
                                f"[AccommodationAgent] LLM 返回为空，使用工具结果: {tool_name}"
                            )
                        else:
                            final_content = final_response.content
                    except Exception as llm_err:
                        final_content = tool_result
                        logger.error(
                            f"[AccommodationAgent] LLM 调用失败: {llm_err}, 使用工具结果"
                        )

                    messages = list(messages)
                    messages.append(AIMessage(content=final_content))

                    travel_plan["accommodation"] = final_content
                else:
                    messages.append(AIMessage(content=f"未找到工具: {tool_name}"))
            else:
                messages = list(messages)
                messages.append(AIMessage(content=response.content))
                travel_plan["accommodation"] = response.content

        except Exception as e:
            error_msg = f"住宿推荐失败: {str(e)}"
            messages = list(messages)
            messages.append(AIMessage(content=error_msg))
            travel_plan["accommodation"] = error_msg

        print(
            f"[DEBUG] AccommodationAgent 返回，travel_plan keys: {list(travel_plan.keys())}"
        )
        return {
            "messages": messages,
            "next_agent": "SUPERVISOR",
            "travel_plan": travel_plan,
        }

    def _get_tool(self, tool_name: str):
        """根据名称获取工具"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None


def create_accommodation_agent(llm: Any) -> Any:
    """创建 Accommodation Agent 的 LangChain Runnable"""

    class AccommodationAgentRunnable:
        def __init__(self, llm: Any):
            self.inner = AccommodationAgent(llm)

        def invoke(self, state: dict, **kwargs: Any) -> dict:
            return self.inner.invoke(state)

        @property
        def name(self) -> str:
            return "AccommodationAgent"

    return AccommodationAgentRunnable(llm)
