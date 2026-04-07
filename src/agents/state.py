"""
Agent 状态定义
使用 TypedDict 定义全局状态，用于 LangGraph Multi-Agent 架构
"""

from typing import Annotated, TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


class AgentState(TypedDict):
    """
    全局 Agent 状态

    Attributes:
        messages: 消息历史，包含所有对话记录
        next_agent: 下一步该调用的 Agent 名称（Supervisor 路由决策）
        travel_plan: 旅游规划状态字典，收集各 Sub-Agent 的结果
        visited_agents: 已访问的 Agent 集合，用于防止重复路由（FIX: BUG-2）
        iteration_count: 迭代计数器，用于防止无限循环（FIX: BUG-5）
        supervisor_error_count: Supervisor 异常计数器（FIX-3: Supervisor失败时使用默认路由）
    """

    messages: Annotated[list, add_messages]  # FIX: 使用 add_messages 代替 lambda
    next_agent: str
    travel_plan: dict
    visited_agents: set  # FIX: 记录已执行的 Agent
    iteration_count: int  # FIX: 迭代计数
    supervisor_error_count: int  # FIX-3: Supervisor 异常计数