"""
景点门票查询Skill
查询景点门票价格、开放时间等信息
使用 LangChain Tool 格式
"""

from langchain_core.tools import tool


@tool
def scenic_ticket(scenic_name: str, date: str = "") -> str:
    """
    查询景点门票价格、开放时间、预约方式等信息。

    Args:
        scenic_name: 景点名称，如：故宫、西湖、泰山
        date: 游玩日期（可选）

    Returns:
        门票信息字符串
    """
    if not scenic_name:
        return "请提供景点名称"

    # TODO: 接入真实景点门票API
    # 模拟数据
    return f"""
{scenic_name}景点信息：

- 门票价格：旺季 ¥60，淡季 ¥40
- 开放时间：08:00-18:00
- 建议游玩时长：3-4小时
- 预约方式：支持现场购票和线上预约
- 最佳游玩季节：春季、秋季
- 特色亮点：自然风光、历史文化

小贴士：
1. 建议提前在线预约，避免排队
2. 携带身份证入园
3. 景区内有多处餐饮点
"""
