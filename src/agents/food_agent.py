"""
美食领域Sub-agent
负责处理餐厅推荐、当地特色美食等需求
"""

from typing import Dict, Any
from openai import OpenAI


class FoodAgent:
    """美食领域Agent"""

    def __init__(self, client: OpenAI):
        self.client = client
        self.model = "moonshotai/Kimi-K2.5"

    def get_system_prompt(self) -> str:
        """获取美食Agent系统提示词"""
        return """你是一个资深的美食评论家。你的专长是：

1. **当地特色**：推荐目的地必吃的特色美食
2. **餐厅推荐**：推荐各价位、各类型的优质餐厅
3. **美食地图**：按区域整理美食分布
4. **觅食攻略**：提供排队避峰、性价比优化等建议

## 输出要求：

请根据用户需求和目的地，提供详细的美食建议，包括：
- 必尝特色美食列表
- 推荐餐厅（含地址、价位、招牌菜）
- 觅食小贴士

请用中文回复。"""

    def execute(self, task: str, context: Dict[str, Any]) -> str:
        """执行美食相关任务"""
        prompt = f"""
图片分析结果：{context.get('image_analysis', '')}
用户任务：{task}

请提供详细的美食推荐。
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )

        return response.choices[0].message.content
