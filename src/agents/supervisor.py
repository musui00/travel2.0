"""
Supervisor 主路由 Agent
负责协调各个 Sub-Agent，决定下一步该调用哪个 Agent
"""

import json
import time
from typing import Any, Literal

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from src.utils.logger import logger

# 定义可路由的 Agent 列表
AGENT_NAMES = ["TransportAgent", "AccommodationAgent", "FoodAgent", "SightseeingAgent"]

# FIX-1: 错误关键字列表
ERROR_KEYWORDS = ["失败", "无法获取", "暂时无法", "错误", "exception", "error", "null"]

# FIX-1: 指数退避配置（秒）
EXPONENTIAL_BACKOFF_DELAYS = [5, 15, 30]  # 第1次等待5s，第2次15s，第3次30s
MAX_MODEL_RETRIES = 2  # 连续失败2次后切换模型


# FIX-1: 自定义异常类型
class RateLimitError(Exception):
    """限流异常 - choices=null 或 HTTP 429"""

    pass


# FIX: 定义路由工具供 Supervisor 使用
@tool
def route_to_agent(agent_name: str, reason: str = "") -> str:
    """
    路由到指定的 Agent 执行任务。

    Args:
        agent_name: 要调用的 Agent 名称（TransportAgent/AccommodationAgent/FoodAgent/SightseeingAgent）
        reason: 路由原因说明

    Returns:
        路由确认信息
    """
    return f"路由到 {agent_name}，原因: {reason}"


@tool
def finish_planning(final_summary: str = "") -> str:
    """
    完成旅游规划，输出最终结果。

    Args:
        final_summary: 最终规划摘要

    Returns:
        完成确认信息
    """
    return f"旅游规划完成"


class Supervisor:
    """Supervisor - 主路由 Agent

    职责：
    1. 接收用户请求
    2. 根据当前状态决定下一步该调用哪个 Sub-Agent
    3. 判断任务是否完成，返回最终结果
    """

    def __init__(self, llm: Any):
        """初始化 Supervisor

        Args:
            llm: LangChain LLM 实例
        """
        self.llm = llm
        self.tools = [route_to_agent, finish_planning]
        self._setup_routing()

    def _setup_routing(self) -> None:
        """设置路由能力 - 绑定工具"""
        if self.tools:
            # FIX: 使用 bind_tools 而非 bind(functions=...)
            self.llm_with_routing = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_routing = self.llm

    def get_system_prompt(self) -> str:
        """获取 Supervisor 系统提示词"""
        return f"""你是一个旅游规划系统的 Supervisor（协调者）。

## 你的职责：
1. 理解用户需求（目标城市、预算、天数、出行日期等）
2. 决定下一步该调用哪个 Sub-Agent 来处理
3. 收集各 Sub-Agent 的结果，最终整合成完整的旅游规划

## 可用的 Sub-Agent：
- **TransportAgent**：处理交通（航班查询、天气查询）- 这是最重要的第一步
- **AccommodationAgent**：处理住宿（酒店、民宿推荐）
- **FoodAgent**：处理美食（餐厅、小吃推荐）
- **SightseeingAgent**：处理景点（景点推荐、门票、本地知识库）

## 路由策略（重要！）：
1. **首次响应**：必须先调用 **route_to_agent** 工具选择 **TransportAgent** 查询天气和航班
   - 用户提供的出发地和目的地城市
   - 用户提供的出行日期
   - 这些信息对于后续规划至关重要
2. 天气和航班查询完成后：调用 **route_to_agent** 选择 **SightseeingAgent** 搜索景点
3. 景点确定后：调用 **route_to_agent** 选择 **AccommodationAgent** 处理住宿
4. 最后：调用 **route_to_agent** 选择 **FoodAgent** 处理美食
5. 所有信息收集完毕：调用 **finish_planning** 完成规划

## 输出要求：
- 必须使用 **route_to_agent** 工具来做出路由决策
- 必须使用 **finish_planning** 工具来结束规划
- 请用中文思考和回复
- 确保首先调用 TransportAgent 获取天气和航班信息！"""

    def invoke(self, state: dict, max_retries: int = 3) -> dict:
        """执行Supervisor路由决策

        Args:
            state: 包含 messages 和 travel_plan 的状态字典
            max_retries: 最大重试次数（默认3次）

        Returns:
            更新后的状态字典（包含 next_agent）
        """
        import json
        import time

        messages = state.get("messages", [])
        travel_plan = state.get("travel_plan", {})
        visited = state.get("visited_agents", set())

        # 获取用户最新消息
        user_input = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_input = msg.content
                break

        # 构建消息列表（包含系统提示和用户输入）
        full_messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=user_input),
        ]

        # 添加已收集的旅游规划信息（帮助决策）
        if travel_plan:
            plan_summary = "已收集的信息：\n"
            for key, value in travel_plan.items():
                if value:  # 只添加非空信息
                    plan_summary += f"- {key}: {value[:100]}...\n"
            full_messages.append(HumanMessage(content=plan_summary))

        # FIX-1: 重试机制 + 指数退避 + 限流根因判断
        retry_count = 0
        last_error = None
        is_rate_limit_error = False  # FIX-4: 标记是否为限流错误

        while retry_count <= max_retries:
            try:
                # 调用 LLM 进行路由决策
                response = self.llm_with_routing.invoke(full_messages)

                # FIX-4: 防御性检查 response，检测 choices=null 畸形响应
                if response is None:
                    # FIX-4: choices=null 返回 None，需要检查响应内容
                    last_error = "LLM 返回 None 响应（可能是限流导致的 choices=null）"
                    logger.error(
                        f"[Supervisor] {last_error}, retry_count={retry_count}"
                    )
                    retry_count += 1
                    # FIX-1: 使用指数退避
                    delay = EXPONENTIAL_BACKOFF_DELAYS[
                        min(retry_count - 1, len(EXPONENTIAL_BACKOFF_DELAYS) - 1)
                    ]
                    time.sleep(delay)
                    is_rate_limit_error = True  # FIX-4: 归类为限流错误
                    continue

                # FIX-4: 检查 response 对象是否有 choices 字段（某些 API 返回空 choices）
                if hasattr(response, "choices") and not response.choices:
                    last_error = "LLM 返回 choices=[]（限流导致的畸形响应）"
                    logger.error(
                        f"[Supervisor] {last_error}, retry_count={retry_count}"
                    )
                    retry_count += 1
                    delay = EXPONENTIAL_BACKOFF_DELAYS[
                        min(retry_count - 1, len(EXPONENTIAL_BACKOFF_DELAYS) - 1)
                    ]
                    time.sleep(delay)
                    is_rate_limit_error = True
                    continue

                # 解析工具调用响应
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

                    # 执行工具
                    tool = self._get_tool(tool_name)
                    if tool:
                        tool_result = tool.invoke(tool_args)

                        messages = list(messages)
                        messages.append(AIMessage(content=f"[调用工具 {tool_name}]"))
                        messages.append(
                            HumanMessage(
                                content=f"工具 {tool_name} 返回: {tool_result}"
                            )
                        )

                        # 解析路由决策
                        if tool_name == "route_to_agent":
                            next_agent = tool_args.get("agent_name", "FINISH")
                            reason = tool_args.get("reason", "通过工具路由")
                        elif tool_name == "finish_planning":
                            next_agent = "FINISH"
                            reason = "完成规划"
                        else:
                            next_agent = "FINISH"
                            reason = "未知工具"
                    else:
                        next_agent = "FINISH"
                        reason = f"未找到工具: {tool_name}"
                        messages = list(messages)
                        messages.append(AIMessage(content=reason))
                else:
                    # FIX: 没有工具调用时，使用智能路由作为后备
                    response_content = getattr(response, "content", None)
                    if response_content is None:
                        last_error = f"LLM 返回 content 为 None（限流导致的畸形响应）"
                        logger.error(f"[Supervisor] {last_error}")
                        retry_count += 1
                        # FIX-1: 使用指数退避
                        delay = EXPONENTIAL_BACKOFF_DELAYS[
                            min(retry_count - 1, len(EXPONENTIAL_BACKOFF_DELAYS) - 1)
                        ]
                        time.sleep(delay)
                        is_rate_limit_error = True
                        continue

                    print(f"[DEBUG] Supervisor 无工具调用: {response_content[:100]}...")
                    next_agent, reason = self._intelligent_routing(travel_plan, visited)

                    messages = list(messages)
                    messages.append(
                        AIMessage(
                            content=f"[Supervisor 路由决策] {reason} -> {next_agent}"
                        )
                    )

                new_travel_plan = dict(travel_plan)
                break  # 成功跳出重试循环

            except Exception as e:
                last_error = str(e)
                # FIX-4: 检查错误类型，识别限流导致的 choices=null
                error_str = str(e).lower()

                # FIX-4: 判断是否为限流错误（优先检测）
                if (
                    "null value for 'choices'" in last_error
                    or "choices is none" in error_str
                ):
                    # FIX-4: choices=null 是限流导致的畸形响应，归类为 RateLimitError
                    logger.error(
                        f"[Supervisor] Rate Limit (choices=null): {last_error}, retry_count={retry_count}"
                    )
                    is_rate_limit_error = True
                    delay = EXPONENTIAL_BACKOFF_DELAYS[
                        min(retry_count, len(EXPONENTIAL_BACKOFF_DELAYS) - 1)
                    ]
                    time.sleep(delay)  # FIX-1: 使用指数退避
                elif (
                    "429" in last_error
                    or "rate limit" in error_str
                    or "rate_limit" in error_str
                ):
                    # FIX-4: HTTP 429 限流错误
                    logger.error(
                        f"[Supervisor] HTTP 429 Rate Limit: {last_error}, retry_count={retry_count}"
                    )
                    is_rate_limit_error = True
                    # FIX-1: 优先使用 retry-after header
                    delay = 5  # 默认等待5s
                    time.sleep(delay)
                else:
                    logger.error(
                        f"[Supervisor] 调用异常: {last_error}, retry_count={retry_count}"
                    )
                    time.sleep(2)

                retry_count += 1
                if retry_count > max_retries:
                    break

        # FIX-1: 重试耗尽后的降级处理
        if retry_count > max_retries and last_error:
            next_agent = "FINISH"
            reason = f"处理出错: {last_error}"
            if is_rate_limit_error:
                reason = f"限流出错: {last_error}"  # FIX-4: 标注限流错误
            messages = list(messages)
            messages.append(AIMessage(content=f"[Supervisor] {reason}"))
            new_travel_plan = dict(travel_plan)
            logger.error(
                f"[Supervisor] 重试{max_retries}次后失败，强制结束（限流错误: {is_rate_limit_error}）"
            )

        print(
            f"[DEBUG] Supervisor 返回，next_agent={next_agent}, travel_plan keys: {list(new_travel_plan.keys())}"
        )
        return {
            "messages": messages,
            "next_agent": next_agent,
            "travel_plan": new_travel_plan,
        }

    def _get_tool(self, tool_name: str):
        """根据名称获取工具"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None

    def _intelligent_routing(self, travel_plan: dict, visited: set = None) -> tuple:
        """智能路由决策 - 根据已收集的信息决定下一步

        Args:
            travel_plan: 已收集的旅游规划信息
            visited: 已访问的 Agent 集合

        Returns:
            (next_agent, reason) 元组
        """
        visited = visited or set()
        collected_keys = set(travel_plan.keys())

        # FIX: 检查已收集的结果是否包含错误信息
        failed_agents = set()
        for key, value in travel_plan.items():
            if value:
                value_str = str(value).lower()
                for error_kw in ERROR_KEYWORDS:
                    if error_kw.lower() in value_str:
                        failed_agents.add(key)
                        logger.warning(
                            f"[Supervisor] 检测到 {key} 返回错误: {value_str[:50]}..."
                        )
                        break

        # 按顺序选择下一个未收集的或执行失败的
        routing_order = [
            ("transport", "TransportAgent", "查询天气和航班"),
            ("sightseeing", "SightseeingAgent", "推荐景点"),
            ("accommodation", "AccommodationAgent", "推荐住宿"),
            ("food", "FoodAgent", "推荐美食"),
        ]

        for key, agent_name, action in routing_order:
            # 跳过已成功完成的（不在 failed_agents 中且已收集）
            if key in collected_keys and key not in failed_agents:
                continue
            # 跳过已访问的
            if agent_name in visited:
                continue
            # 选择未完成或失败的
            print(
                f"[DEBUG] 智能路由：已收集 {list(collected_keys)}，失败 {list(failed_agents)}，选择 {agent_name}"
            )
            return agent_name, f"继续 {action}"

        # 所有信息已收集且无失败
        return "FINISH", "已收集所有信息，任务完成"

    def should_continue(self, state: dict) -> bool:
        """判断是否继续执行

        Args:
            state: 当前状态

        Returns:
            True 表示继续，False 表示完成
        """
        return state.get("next_agent", "FINISH") != "FINISH"


def create_supervisor(llm: Any) -> Any:
    """创建 Supervisor 的 LangChain Runnable"""

    class SupervisorRunnable:
        def __init__(self, llm: Any):
            self.inner = Supervisor(llm)

        def invoke(self, state: dict, **kwargs: Any) -> dict:
            return self.inner.invoke(state)

        @property
        def name(self) -> str:
            return "Supervisor"

    return SupervisorRunnable(llm)
