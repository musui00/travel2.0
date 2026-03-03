"""
天气查询Skill
调用外部天气API查询目的地天气
使用 LangChain Tool 格式
"""

from langchain_core.tools import tool


@tool
def weather_query(city: str) -> str:
    """
    查询指定城市的天气情况，用于出行规划参考。

    Args:
        city: 要查询的城市名称，如：北京、上海、杭州

    Returns:
        天气信息字符串
    """
    # TODO: 这里可以接入真实的天气API
    # 例如：和风天气、天气API等
    # 示例使用占位数据

    if not city:
        return "请提供城市名称"

    weather_info = f"""
{city}今日天气：
- 天气：晴
- 温度：18-25°C
- 空气质量：优
- 出行建议：适合户外活动，请注意防晒
"""
    return weather_info
