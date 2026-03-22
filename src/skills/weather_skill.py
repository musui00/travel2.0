"""
天气查询Skill
调用外部天气API查询目的地天气
使用 LangChain Tool 格式
使用 wttr.in 免费天气 API
"""

import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

# 加载环境变量
load_dotenv()

# wttr.in 天气 API（免费，无需 API Key）
WEATHER_API_URL = "https://wttr.in"


def query_weather(city: str) -> dict:
    """
    查询天气数据

    Args:
        city: 城市名称

    Returns:
        天气数据字典
    """
    url = f"{WEATHER_API_URL}/{city}"
    params = {
        "format": "j1"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

    return {}


@tool
def weather_query(city: str) -> str:
    """
    查询指定城市的天气情况，用于出行规划参考。返回当前天气和未来3天预报。

    Args:
        city: 要查询的城市名称，如：北京、上海、杭州、厦门

    Returns:
        天气信息字符串
    """
    if not city:
        return "请提供城市名称"

    # 查询天气
    weather_data = query_weather(city)

    if not weather_data or "data" not in weather_data:
        return f"未找到城市：{city}，请检查城市名称是否正确"

    try:
        current = weather_data["data"]["current_condition"][0]
        weather_forecast = weather_data["data"]["weather"]

        # 当前天气
        temp_c = current.get("temp_C", "?")
        weather_desc = current.get("weatherDesc", [{}])[0].get("value", "-")
        humidity = current.get("humidity", "?")
        wind_speed = current.get("windspeedKmph", "?")
        wind_dir = current.get("winddir16Point", "-")
        visibility = current.get("visibility", "?")
        uv_index = current.get("uvIndex", "?")

        weather_info = f"【{city}天气预报】\n\n"
        weather_info += f"🌡️ 当前天气：\n"
        weather_info += f"   温度: {temp_c}°C\n"
        weather_info += f"   天气: {weather_desc}\n"
        weather_info += f"   湿度: {humidity}%\n"
        weather_info += f"   风力: {wind_dir} {wind_speed} km/h\n"
        weather_info += f"   能见度: {visibility} km\n"
        weather_info += f"   紫外线: {uv_index}\n\n"

        # 未来3天预报
        weather_info += f"📅 未来3天预报：\n\n"

        for day in weather_forecast[:3]:
            date = day.get("date", "")
            maxtemp = day.get("maxtempC", "?")
            mintemp = day.get("mintempC", "?")
            avg_temp = day.get("avgtempC", "?")
            sunrise = day.get("astronomy", [{}])[0].get("sunrise", "-")
            sunset = day.get("astronomy", [{}])[0].get("sunset", "-")

            # 获取白天天气描述
            hourly = day.get("hourly", [{}])
            if hourly:
                day_weather = hourly[0].get("weatherDesc", [{}])[0].get("value", "-")
            else:
                day_weather = "-"

            weather_info += f"""📆 {date}
   温度: {mintemp}°C ~ {maxtemp}°C (平均 {avg_temp}°C)
   天气: {day_weather}
   日出: {sunrise} | 日落: {sunset}
---

"""

        # 出行建议
        temp = int(temp_c) if temp_c != "?" else 20
        if "雨" in weather_desc:
            advice = "建议携带雨具，注意出行安全"
        elif "雪" in weather_desc:
            advice = "建议注意防滑保暖"
        elif "晴" in weather_desc and temp > 30:
            advice = "天气炎热，建议做好防晒"
        elif "晴" in weather_desc and temp < 10:
            advice = "天气较凉，建议添加外套"
        else:
            advice = "适合户外活动"

        weather_info += f"💡 出行建议：{advice}\n"
        weather_info += f"\n数据来源：wttr.in"

        return weather_info

    except Exception as e:
        return f"解析天气数据失败: {str(e)}，请检查城市名称是否正确"
