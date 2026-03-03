"""
航班查询Skill
调用外部航班API查询航班信息
使用 LangChain Tool 格式
"""

from langchain_core.tools import tool


@tool
def flight_search(from_city: str, to_city: str, date: str = "") -> str:
    """
    查询航班信息，包括起降时间、价格、航空公司等。

    Args:
        from_city: 出发城市
        to_city: 目的城市
        date: 出发日期，格式YYYY-MM-DD（可选）

    Returns:
        航班信息字符串
    """
    if not from_city or not to_city:
        return "请提供出发城市和目的城市"

    # TODO: 这里可以接入真实的航班API
    # 例如：航旅纵横、飞常准等
    # 模拟数据
    flights = [
        {
            "airline": "东方航空 MU",
            "flight_no": "MU1234",
            "departure": "08:00",
            "arrival": "10:30",
            "duration": "2h30m",
            "price": "¥580",
            "type": "经济舱",
        },
        {
            "airline": "南方航空 CZ",
            "flight_no": "CZ5678",
            "departure": "14:00",
            "arrival": "16:25",
            "duration": "2h25m",
            "price": "¥650",
            "type": "经济舱",
        },
        {
            "airline": "国航 CA",
            "flight_no": "CA9012",
            "departure": "19:30",
            "arrival": "21:55",
            "duration": "2h25m",
            "price": "¥720",
            "type": "经济舱",
        },
    ]

    result = f"从 {from_city} 到 {to_city} 的航班信息：\n\n"

    for i, f in enumerate(flights, 1):
        result += f"""### 航班 {i}
- 航空公司：{f['airline']}
- 航班号：{f['flight_no']}
- 起飞时间：{f['departure']}
- 到达时间：{f['arrival']}
- 飞行时长：{f['duration']}
- 价格：{f['price']}
- 舱位：{f['type']}

"""

    return result
