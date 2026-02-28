"""
住宿领域Sub-agent
负责处理酒店、民宿等住宿相关需求
"""

from typing import Dict, Any
from openai import OpenAI


class AccommodationAgent:
    """住宿领域Agent"""

    def __init__(self, client: OpenAI):
        self.client = client
        self.model = "moonshotai/Kimi-K2.5"

    def get_system_prompt(self) -> str:
        """获取住宿Agent系统提示词"""
        return """你是一个专业的酒店预订顾问。你的专长是：

1. **酒店推荐**：根据目的地和预算推荐合适酒店
2. **民宿选择**：提供特色民宿、性价比高的选择
3. **区域分析**：分析各区域优劣势，帮助选择最佳住宿位置
4. **预订建议**：提供预订时机、注意事项等建议

## 输出要求：

请根据用户需求，提供详细的住宿建议，包括：
- 推荐住宿区域
- 具体酒店/民宿推荐（可包含价格范围）
- 推荐理由
- 预订注意事项

请用中文回复。"""

    def execute(self, task: str, context: Dict[str, Any]) -> str:
        """执行住宿相关任务"""
        prompt = f"""
图片分析结果：{context.get('image_analysis', '')}
用户任务：{task}

请提供详细的住宿建议。
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
