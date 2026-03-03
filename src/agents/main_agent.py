"""
主Agent - 使用 LangChain Agent
负责理解用户意图，调用工具，生成旅游规划
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain import agent
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.skills import get_all_tools


class MainAgent:
    """主Agent：使用 LangChain 架构"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tools = get_all_tools()
        self.agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        """创建 LangChain Agent"""
        # 系统提示词
        system_message = """你是一个智能旅游规划助手。你的职责是：

1. **理解用户需求**：分析用户的旅游需求
2. **调用工具**：使用可用的工具查询信息（天气、航班、景点门票）
3. **生成规划**：根据查询结果生成完整的旅游规划

## 可用工具：
- weather_query：查询城市天气
- flight_search：查询航班信息
- scenic_ticket：查询景点门票信息

## 工作流程：
1. 接收用户需求（可能包含图片分析结果）
2. 根据需要调用相关工具获取信息
3. 整合所有信息，生成完整的旅游规划

请用中文回复，确保规划详细、实用。"""

        # 创建 prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 创建 Agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        # 创建 AgentExecutor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
        )

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

        # 执行 Agent
        try:
            result = self.agent_executor.invoke({"input": input_text})
            return result["output"]
        except Exception as e:
            return f"处理过程中出现错误：{str(e)}"
