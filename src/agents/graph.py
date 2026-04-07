"""
LangGraph 工作流构建
使用 Supervisor 模式协调多个 Sub-Agent
"""

import time
from functools import partial
from typing import Any, Literal

from langgraph.graph import StateGraph, END
from langgraph.constants import Send

# 导入状态定义
from src.agents.state import AgentState

# 导入各个 Agent
from src.agents.supervisor import Supervisor, create_supervisor
from src.agents.transport_agent import TransportAgent, create_transport_agent
from src.agents.accommodation_agent import (
    AccommodationAgent,
    create_accommodation_agent,
)
from src.agents.food_agent import FoodAgent, create_food_agent
from src.agents.sightseeing_agent import SightseeingAgent, create_sightseeing_agent

# ============================================================================
# FIX-3: Supervisor 失败时的硬编码默认路由顺序
# ============================================================================

# FIX-3: 默认路由顺序（Supervisor 异常时使用）
DEFAULT_ROUTING_ORDER = [
    "TransportAgent",
    "AccommodationAgent",
    "FoodAgent",
    "SightseeingAgent",
]

# FIX-1: 指数退避配置（秒）
EXPONENTIAL_BACKOFF_DELAYS = [5, 15, 30]  # 第1次5s，第2次15s，第3次30s


# ============================================================================
# Node Functions - 各个节点的执行逻辑
# ============================================================================


def supervisor_node(state: AgentState, supervisor: Any) -> AgentState:
    """Supervisor 节点 - 决定下一步路由

    FIX-3: Supervisor 异常时，使用硬编码的默认路由顺序依次执行

    Args:
        state: 当前状态
        supervisor: Supervisor 实例

    Returns:
        更新后的状态
    """
    # FIX-1: 避免 rate limit（全局降频）
    time.sleep(1)

    # FIX-3: 记录异常计数
    supervisor_error_count = state.get("supervisor_error_count", 0)

    # FIX-3: 尝试调用 Supervisor，使用增强的错误处理
    try:
        result = supervisor.invoke(state)
        result["iteration_count"] = state.get("iteration_count", 0) + 1
        # FIX-3: 重置错误计数
        result["supervisor_error_count"] = 0
        return result
    except Exception as e:
        # FIX-3: Supervisor 异常，使用硬编码默认路由
        error_msg = str(e)
        supervisor_error_count += 1

        print(f"[DEBUG] Supervisor 执行失败: {error_msg}")

        # FIX-1: 指数退避等待
        delay = EXPONENTIAL_BACKOFF_DELAYS[
            min(supervisor_error_count - 1, len(EXPONENTIAL_BACKOFF_DELAYS) - 1)
        ]
        print(f"[DEBUG] 等待 {delay}s 后使用默认路由...")
        time.sleep(delay)

        # FIX-3: 获取当前已访问的 Agent
        visited = set(state.get("visited_agents", set()))
        new_travel_plan = dict(state.get("travel_plan", {}))

        # FIX-3: 从默认路由顺序中选择下一个未访问的 Agent
        next_agent = None
        reason = ""
        for agent_name in DEFAULT_ROUTING_ORDER:
            if agent_name not in visited:
                next_agent = agent_name
                reason = f"Supervisor异常，使用默认路由: {agent_name}"
                print(f"[DEBUG] {reason}")
                break

        # FIX-3: 所有 Agent 都已访问，强制结束
        if not next_agent:
            next_agent = "FINISH"
            reason = "所有Agent已执行完成"

        return {
            "messages": state.get("messages", []),
            "next_agent": next_agent,
            "travel_plan": new_travel_plan,
            "visited_agents": visited,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "supervisor_error_count": supervisor_error_count,  # FIX-3: 传递错误计数
        }


def transport_node(state: AgentState, transport_agent: Any) -> AgentState:
    """Transport Agent 节点

    Args:
        state: 当前状态
        transport_agent: TransportAgent 实例

    Returns:
        更新后的状态
    """
    # FIX: BUG-3 避免 rate limit
    time.sleep(1)

    result = transport_agent.invoke(state)
    # FIX: BUG-2 记录已访问的 Agent
    visited = set(state.get("visited_agents", set()))
    visited.add("TransportAgent")
    result["visited_agents"] = visited
    return result


def accommodation_node(state: AgentState, accommodation_agent: Any) -> AgentState:
    """Accommodation Agent 节点

    Args:
        state: 当前状态
        accommodation_agent: AccommodationAgent 实例

    Returns:
        更新后的状态
    """
    # FIX: BUG-3 避免 rate limit
    time.sleep(1)

    result = accommodation_agent.invoke(state)
    # FIX: BUG-2 记录已访问的 Agent
    visited = set(state.get("visited_agents", set()))
    visited.add("AccommodationAgent")
    result["visited_agents"] = visited
    return result


def food_node(state: AgentState, food_agent: Any) -> AgentState:
    """Food Agent 节点

    Args:
        state: 当前状态
        food_agent: FoodAgent 实例

    Returns:
        更新后的状态
    """
    # FIX: BUG-3 避免 rate limit
    time.sleep(1)

    result = food_agent.invoke(state)
    # FIX: BUG-2 记录已访问的 Agent
    visited = set(state.get("visited_agents", set()))
    visited.add("FoodAgent")
    result["visited_agents"] = visited
    return result


def sightseeing_node(state: AgentState, sightseeing_agent: Any) -> AgentState:
    """Sightseeing Agent 节点

    Args:
        state: 当前状态
        sightseeing_agent: SightseeingAgent 实例

    Returns:
        更新后的状态
    """
    # FIX: BUG-3 避免 rate limit
    time.sleep(1)

    result = sightseeing_agent.invoke(state)
    # FIX: BUG-2 记录已访问的 Agent
    visited = set(state.get("visited_agents", set()))
    visited.add("SightseeingAgent")
    result["visited_agents"] = visited
    return result


# ============================================================================
# 路由函数 - Supervisor 的条件跳转
# ============================================================================


def route_supervisor(
    state: AgentState,
) -> Literal["transport", "accommodation", "food", "sightseeing", "__end__"]:
    """Supervisor 路由决策

    根据 next_agent 字段决定下一步该调用哪个 Agent

    Args:
        state: 当前状态

    Returns:
        下一个 Agent 的名称（节点名）
    """
    next_agent = state.get("next_agent", "FINISH")
    visited = state.get("visited_agents", set())
    iteration = state.get("iteration_count", 0)
    travel_plan = state.get("travel_plan", {})

    # 最大迭代次数保护
    MAX_ITERATIONS = 10
    if iteration >= MAX_ITERATIONS:
        print(f"[DEBUG] 达到最大迭代次数 {MAX_ITERATIONS}，强制结束")
        return "__end__"

    # FIX: 错误关键字列表
    ERROR_KEYWORDS = [
        "失败",
        "无法获取",
        "暂时无法",
        "错误",
        "exception",
        "error",
        "null",
        "none",
    ]

    # FIX: 检查 travel_plan 是否有失败的结果，强制重试
    failed_keys = []
    for key, value in travel_plan.items():
        if value and isinstance(value, str):
            value_lower = value.lower()
            for error_kw in ERROR_KEYWORDS:
                if error_kw in value_lower:
                    failed_keys.append(key)
                    break

    if failed_keys:
        print(f"[DEBUG] 检测到失败的 Agent: {failed_keys}，强制重试")
        # 移除已访问标记中对应的 agent，以便重试
        agent_remap = {
            "transport": "TransportAgent",
            "sightseeing": "SightseeingAgent",
            "accommodation": "AccommodationAgent",
            "food": "FoodAgent",
        }
        for key in failed_keys:
            agent_name = agent_remap.get(key)
            if agent_name and agent_name in visited:
                visited = visited - {agent_name}
        # 返回重新路由
        state = {**state, "visited_agents": visited}

    # 映射 Agent 名称到节点名
    agent_to_node = {
        "TransportAgent": "transport",
        "AccommodationAgent": "accommodation",
        "FoodAgent": "food",
        "SightseeingAgent": "sightseeing",
        "SUPERVISOR": "supervisor",
        "FINISH": "__end__",
    }

    # 防止重复路由
    if next_agent != "FINISH" and next_agent in visited:
        print(f"[DEBUG] Agent {next_agent} 已访问过，使用智能路由...")
        # 使用智能路由选择下一个
        remaining = [
            "TransportAgent",
            "SightseeingAgent",
            "AccommodationAgent",
            "FoodAgent",
        ]
        for agent in list(remaining):
            if agent in visited:
                remaining.remove(agent)
        if remaining:
            next_agent = remaining[0]
        else:
            next_agent = "FINISH"

    print(
        f"[DEBUG] route_supervisor: next_agent = {next_agent}, visited = {visited}, iteration = {iteration}"
    )

    return agent_to_node.get(next_agent, "__end__")


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """判断是否继续执行

    Args:
        state: 当前状态

    Returns:
        "continue" 继续循环，"end" 结束
    """
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "FINISH":
        return "end"
    return "continue"


# ============================================================================
# 构建 LangGraph
# ============================================================================


def create_graph(llm: Any) -> Any:
    """创建 LangGraph 工作流

    Args:
        llm: LangChain LLM 实例

    Returns:
        编译后的 LangGraph app
    """
    # 创建各个 Agent 实例
    supervisor = Supervisor(llm)
    transport_agent = TransportAgent(llm)
    accommodation_agent = AccommodationAgent(llm)
    food_agent = FoodAgent(llm)
    sightseeing_agent = SightseeingAgent(llm)

    # 使用 partial 绑定 agent 实例到节点函数
    supervisor_node_fn = partial(supervisor_node, supervisor=supervisor)
    transport_node_fn = partial(transport_node, transport_agent=transport_agent)
    accommodation_node_fn = partial(
        accommodation_node, accommodation_agent=accommodation_agent
    )
    food_node_fn = partial(food_node, food_agent=food_agent)
    sightseeing_node_fn = partial(sightseeing_node, sightseeing_agent=sightseeing_agent)

    # 创建状态图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node_fn)
    workflow.add_node("transport", transport_node_fn)
    workflow.add_node("accommodation", accommodation_node_fn)
    workflow.add_node("food", food_node_fn)
    workflow.add_node("sightseeing", sightseeing_node_fn)

    # 设置入口点
    workflow.set_entry_point("supervisor")

    # 添加条件边：Supervisor -> 根据决策路由
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "transport": "transport",
            "accommodation": "accommodation",
            "food": "food",
            "sightseeing": "sightseeing",
            "supervisor": "supervisor",  # 重新调用 Supervisor
            "__end__": END,
        },
    )

    # 添加无条件边：各 Sub-Agent -> 返回 Supervisor
    for node in ["transport", "accommodation", "food", "sightseeing"]:
        workflow.add_edge(node, "supervisor")

    # 编译图
    app = workflow.compile()

    return app


# ============================================================================
# 便捷函数
# ============================================================================


def create_travel_planner(llm: Any) -> Any:
    """创建旅游规划器的便捷函数

    Args:
        llm: LangChain LLM 实例

    Returns:
        可调用的旅游规划器
    """
    return create_graph(llm)


# 导出
__all__ = [
    "create_graph",
    "create_travel_planner",
    "AgentState",
]
