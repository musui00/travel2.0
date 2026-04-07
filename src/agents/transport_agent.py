"""
交通领域 Sub-Agent
负责处理航班、天气等交通相关需求
"""

import json
import time
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from src.skills import weather_query, flight_search
from src.utils.logger import logger

# FIX-1: 指数退避配置
EXPONENTIAL_BACKOFF_DELAYS = [5, 15, 30]


class TransportAgent:
    """交通领域 Agent - 处理航班和天气查询"""

    def __init__(self, llm: Any):
        """初始化 Transport Agent

        Args:
            llm: LangChain LLM 实例
        """
        self.llm = llm
        self.tools = [weather_query, flight_search]
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
        return """你是一个专业的交通出行顾问。

## 你的专长：
1. 航班查询：根据出发城市、目的城市、日期查询航班信息
2. 天气查询：查询目的地在特定日期的天气情况，影响出行决策

## 你可以使用的工具：
- weather_query：查询城市天气（需要城市名称参数）
- flight_search：查询航班信息（需要 from_city:出发城市, to_city:目的城市, date:出发日期）

## 重要参数说明：
- flight_search 的 from_city 参数是出发城市（如用户现处城市）
- flight_search 的 to_city 参数是目的城市（如用户要去的目标城市）
- 用户请求中会包含这些信息，请务必正确提取并传递给工具

## 输出要求：
请根据用户需求调用合适的工具，然后基于工具返回结果给出交通建议。
请用中文回复。"""

    def invoke(self, state: dict, max_retries: int = 2) -> dict:
        """执行交通任务，调用工具并更新状态

        Args:
            state: 包含 messages 和 travel_plan 的状态字典
            max_retries: 最大重试次数（默认2次）

        Returns:
            更新后的状态字典
        """
        messages = state.get("messages", [])
        travel_plan = state.get("travel_plan", {})

        # 获取用户最新请求
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

        # FIX: 重试机制 + 防御性处理
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                response = self.llm_with_tools.invoke(full_messages)

                # FIX: 防御性检查 response 是否为 None
                if response is None:
                    last_error = "LLM 返回 None 响应"
                    logger.error(f"[TransportAgent] {last_error}, retry_count={retry_count}")
                    retry_count += 1
                    continue

                # 检查是否有函数调用
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
                        function_call = {
                            "name": tool_name,
                            "arguments": arguments
                        }
                elif hasattr(response, "additional_kwargs") and response.additional_kwargs.get(
                    "function_call"
                ):
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
                        tool_result = tool.invoke(tool_args)

                        # FIX: 直接返回工具结果，不依赖第二次 LLM 调用（避免 rate limit）
                        # 构造格式化的响应
                        result_summary = f"【{tool_name}】\n{tool_result}"

                        messages = list(messages)
                        messages.append(AIMessage(content=result_summary))

                        new_travel_plan = dict(travel_plan)
                        new_travel_plan["transport"] = result_summary
                        travel_plan = new_travel_plan
                    else:
                        messages.append(AIMessage(content=f"未找到工具: {tool_name}"))
                else:
                    # 无需调用工具，直接返回结果
                    # FIX: 防御性检查 response.content
                    content = getattr(response, "content", None)
                    if content is None:
                        last_error = f"LLM 返回 content 为 None: {response}"
                        logger.error(f"[TransportAgent] {last_error}")
                        retry_count += 1
                        time.sleep(2)
                        continue

                    messages = list(messages)
                    messages.append(AIMessage(content=content))
                    new_travel_plan = dict(travel_plan)
                    new_travel_plan["transport"] = content
                    travel_plan = new_travel_plan

                # 成功跳出重试循环
                break

            except Exception as e:
                last_error = str(e)
                logger.error(f"[TransportAgent] 调用异常: {last_error}, retry_count={retry_count}")
                # FIX-1: 使用指数退避
                error_str = str(e).lower()
                if "null value for 'choices'" in last_error or "choices is none" in error_str:
                    delay = EXPONENTIAL_BACKOFF_DELAYS[min(retry_count, len(EXPONENTIAL_BACKOFF_DELAYS) - 1)]
                    logger.error(f"[TransportAgent] Rate Limit (choices=null): {last_error}")
                    time.sleep(delay)
                elif "429" in last_error or "rate limit" in error_str:
                    time.sleep(5)  # rate limit
                else:
                    time.sleep(2)
                retry_count += 1
                if retry_count > max_retries:
                    break

        # FIX: 重试耗尽后的降级处理
        if retry_count > max_retries and last_error:
            error_msg = f"交通信息暂时无法获取，请稍后重试。({last_error})"
            logger.error(f"[TransportAgent] 重试{ max_retries}次后失败: {error_msg}")
            messages = list(messages)
            messages.append(AIMessage(content=error_msg))
            new_travel_plan = dict(travel_plan)
            new_travel_plan["transport"] = error_msg
            travel_plan = new_travel_plan

        # 返回更新后的状态
        logger.info(f"[DEBUG] TransportAgent 返回，travel_plan keys: {list(travel_plan.keys())}")
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


# 导出 Runnable（用于 LangGraph）
transport_agent_runnable = None


def create_transport_agent(llm: Any) -> Any:
    """创建 Transport Agent 的 LangChain Runnable

    Args:
        llm: LangChain LLM 实例

    Returns:
        可调用的 Agent
    """
    global transport_agent_runnable

    class TransportAgentRunnable:
        """Transport Agent 的 Runnable 包装"""

        def __init__(self, llm: Any):
            self.inner = TransportAgent(llm)

        def invoke(self, state: dict, **kwargs: Any) -> dict:
            return self.inner.invoke(state)

        @property
        def name(self) -> str:
            return "TransportAgent"

    transport_agent_runnable = TransportAgentRunnable(llm)
    return transport_agent_runnable