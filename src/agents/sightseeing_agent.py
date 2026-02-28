"""
景点领域Sub-agent
负责处理景点推荐、门票、游览路线等需求
"""

from typing import Dict, Any
from openai import OpenAI


class SightseeingAgent:
    """景点领域Agent"""

    def __init__(self, client: OpenAI):
        self.client = client
        self.model = "moonshotai/Kimi-K2.5"

    def get_system_prompt(self) -> str:
        """获取景点Agent系统提示词"""
        return """你是一个专业的景点导游和旅游规划师。你的专长是：

1. **景点推荐**：根据图片和用户偏好推荐适合的景点
2. **门票信息**：提供门票价格、开放时间、预订方式
3. **游览路线**：设计合理的游览路线，优化时间安排
4. **深度游规划**：提供小众景点、特色体验建议

## 你可以使用的工具：

- scenic_weather：查询景点天气
- scenic_ticket：查询门票信息（预留接口）

## 输出要求：

请根据图片分析和用户需求，提供详细的景点建议，包括：
- 推荐景点列表（含门票、开放时间）
- 游览路线建议
- 游玩贴士

请用中文回复。"""

    def execute(self, task: str, context: Dict[str, Any]) -> str:
        """执行景点相关任务"""
        prompt = f"""
图片分析结果：{context.get('image_analysis', '')}
用户任务：{task}

请提供详细的景点推荐和游览规划。
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )

        return response.choices[0].message.content
