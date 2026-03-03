"""
主Agent - 全局路由与任务分发
负责理解用户意图，拆解任务，并发调度Sub-agent
"""

import json
from typing import Dict, List, Any, Optional
from openai import OpenAI

# 导入Sub-agent
from src.agents.transport_agent import TransportAgent
from src.agents.accommodation_agent import AccommodationAgent
from src.agents.sightseeing_agent import SightseeingAgent
from src.agents.food_agent import FoodAgent


class MainAgent:
    """主Agent：负责全局路由和任务分发"""

    def __init__(self, client: OpenAI):
        self.client = client
        self.model = "moonshotai/Kimi-K2.5"

        # 初始化Sub-agent
        self.transport_agent = TransportAgent(client)
        self.accommodation_agent = AccommodationAgent(client)
        self.sightseeing_agent = SightseeingAgent(client)
        self.food_agent = FoodAgent(client)

    def get_system_prompt(self) -> str:
        """获取主Agent系统提示词"""
        return """你是一个智能旅游规划助手的主控Agent。你的职责是：

1. **理解用户意图**：分析用户的需求，确定需要哪些方面的帮助
2. **任务拆解**：将复杂需求拆分为多个子任务
3. **路由分发**：将子任务分发给对应的垂直领域Sub-agent处理
4. **结果整合**：汇总各Sub-agent的结果，形成完整方案

## 可用的Sub-agent：

- **transport_agent**：处理交通相关需求（航班、高铁、租车等）
- **accommodation_agent**：处理住宿相关需求（酒店、民宿、推荐等）
- **sightseeing_agent**：处理景点相关需求（景点推荐、门票、游览路线）
- **food_agent**：处理美食相关需求（餐厅推荐、当地特色美食）

## 工作流程：

1. 接收用户输入（图片分析结果 + 用户需求）
2. 判断需要哪些Sub-agent参与
3. 并发调用相关Sub-agent
4. 整合所有结果，输出完整旅游规划

## 输出格式：

请以JSON格式输出任务分配结果：
{
    "tasks": [
        {"agent": "transport_agent", "task": "具体任务描述"},
        {"agent": "accommodation_agent", "task": "具体任务描述"}
    ]
}

请用中文回复。"""

    def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """分析用户意图，拆解任务"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": user_input},
            ],
            stream=False,
        )

        content = response.choices[0].message.content

        # 尝试解析JSON
        try:
            # 查找JSON部分
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 默认返回需要所有agent处理
        return {
            "tasks": [
                {"agent": "sightseeing_agent", "task": "根据图片推荐景点"},
                {"agent": "transport_agent", "task": "查询交通方式"},
                {"agent": "accommodation_agent", "task": "推荐住宿"},
                {"agent": "food_agent", "task": "推荐当地美食"},
            ]
        }

    def execute_tasks(
        self, tasks: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """并发执行所有任务"""
        import concurrent.futures

        results = {}

        def run_agent(agent_name: str, task: str):
            """运行单个Agent"""
            if agent_name == "transport_agent":
                return self.transport_agent.execute(task, context)
            elif agent_name == "accommodation_agent":
                return self.accommodation_agent.execute(task, context)
            elif agent_name == "sightseeing_agent":
                return self.sightseeing_agent.execute(task, context)
            elif agent_name == "food_agent":
                return self.food_agent.execute(task, context)
            return {"error": f"Unknown agent: {agent_name}"}

        # 并发执行所有任务
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_task = {
                executor.submit(run_agent, task["agent"], task["task"]): task
                for task in tasks
            }

            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                agent_name = task["agent"]
                try:
                    results[agent_name] = future.result()
                except Exception as e:
                    results[agent_name] = {"error": str(e)}

        return results

    def integrate_results(self, results: Dict[str, Any]) -> str:
        """整合所有Sub-agent结果，生成最终规划"""
        integration_prompt = """请整合以下各领域专家的建议，生成一份完整、连贯的旅游规划。

需要整合的内容：
"""

        for agent_name, result in results.items():
            agent_display_name = {
                "transport_agent": "交通专家",
                "accommodation_agent": "住宿专家",
                "sightseeing_agent": "景点专家",
                "food_agent": "美食专家",
            }.get(agent_name, agent_name)

            integration_prompt += f"\n## {agent_display_name}的建议：\n{result}\n"

        integration_prompt += """
请生成一份完整、实用的旅游规划，包含：
1. 行程概述
2. 每日详细安排
3. 费用预算（可选）
4. 实用贴士

请用中文回复，格式清晰美观。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的旅游规划整合专家。"},
                {"role": "user", "content": integration_prompt},
            ],
            stream=True,
        )

        result = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                result += chunk.choices[0].delta.content

        return result

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
        print("【主Agent】开始分析用户意图...")
        print("=" * 60)

        # 构建上下文
        context = {"image_analysis": image_analysis, "user_input": user_input}

        # 1. 分析意图，拆解任务
        task_config = self.analyze_intent(
            f"图片分析：{image_analysis}\n用户需求：{user_input}"
        )

        print(f"\n任务拆解结果：")
        for task in task_config.get("tasks", []):
            print(f"  - {task['agent']}: {task['task']}")

        # 2. 并发执行所有子任务
        print("\n" + "=" * 60)
        print("【主Agent】并发调度Sub-agent处理任务...")
        print("=" * 60)

        results = self.execute_tasks(task_config.get("tasks", []), context)

        # 3. 展示各Agent结果
        for agent_name, result in results.items():
            print(f"\n--- {agent_name} 结果 ---")
            if isinstance(result, dict) and "error" in result:
                print(f"错误: {result['error']}")
            else:
                print(result[:500] + "..." if len(str(result)) > 500 else result)

        # 4. 整合结果
        print("\n" + "=" * 60)
        print("【主Agent】整合各领域建议，生成最终规划...")
        print("=" * 60)

        final_plan = self.integrate_results(results)

        return final_plan
