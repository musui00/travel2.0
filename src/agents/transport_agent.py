"""
交通领域Sub-agent
负责处理航班、高铁、租车等交通相关需求
"""

from typing import Dict, Any
from openai import OpenAI

# 导入Skill工具
from src.skills.flight_skill import FlightSkill
from src.skills.weather_skill import WeatherSkill


class TransportAgent:
    """交通领域Agent"""

    def __init__(self, client: OpenAI):
        self.client = client
        self.model = "moonshotai/Kimi-K2.5"
        self.flight_skill = FlightSkill()
        self.weather_skill = WeatherSkill()

    def get_system_prompt(self) -> str:
        """获取交通Agent系统提示词"""
        return """你是一个专业的交通出行顾问。你的专长是：

1. **航班查询**：提供航班信息、价格比较、中转建议
2. **高铁/火车**：提供铁路时刻表、路线规划
3. **租车服务**：提供租车公司、费用估算
4. **自驾规划**：提供自驾路线、路况信息
5. **综合交通方案**：结合多种交通方式提供最优方案

## 你可以使用的工具：

- flight_search：查询航班信息
- weather_query：查询目的地天气（影响出行决策）

## 输出要求：

请根据用户需求，提供详细的交通建议，包括：
- 推荐交通方式
- 预计时间和费用
- 注意事项

请用中文回复。"""

    def execute(self, task: str, context: Dict[str, Any]) -> str:
        """执行交通相关任务"""
        # 构建提示词
        prompt = f"""
图片分析结果：{context.get('image_analysis', '')}
用户任务：{task}

请提供详细的交通建议。如果需要查询航班或天气，请先调用相关工具。
"""

        # 先尝试调用Skill工具获取实时数据
        additional_info = []

        # 示例：调用天气技能
        # weather_result = self.weather_skill.execute({"city": "北京"})
        # if weather_result:
        #     additional_info.append(f"天气情况：{weather_result}")

        if additional_info:
            prompt += f"\n\n实时信息：\n" + "\n".join(additional_info)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )

        return response.choices[0].message.content
