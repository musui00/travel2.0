"""
住宿推荐 Skill
根据目的地和偏好推荐酒店/民宿
使用 LangChain Tool 格式
支持高德地图 API 实时搜索
"""

from typing import Dict, List
from langchain_core.tools import tool

from src.utils.amap_service import get_amap_service

# 酒店数据库
HOTEL_DATABASE = {
    "上海": {
        "豪华": [
            {
                "name": "上海外滩华尔道夫酒店",
                "area": "外滩",
                "price": "¥2000-3000",
                "rating": "4.9",
                "features": "江景房、历史建筑",
            },
            {
                "name": "上海浦东丽思卡尔顿",
                "area": "陆家嘴",
                "price": "¥2500-4000",
                "rating": "4.8",
                "features": "顶层天际线景观",
            },
            {
                "name": "和平饭店",
                "area": "外滩",
                "price": "¥1800-2500",
                "rating": "4.7",
                "features": "百年历史、地标建筑",
            },
        ],
        "舒适": [
            {
                "name": "上海外滩郁锦香酒店",
                "area": "外滩",
                "price": "¥600-900",
                "rating": "4.5",
                "features": "性价比高、交通便利",
            },
            {
                "name": "全季酒店(南京路步行街店)",
                "area": "南京路",
                "price": "¥400-600",
                "rating": "4.4",
                "features": "位置极佳",
            },
            {
                "name": "亚朵酒店(人民广场店)",
                "area": "人民广场",
                "price": "¥500-700",
                "rating": "4.6",
                "features": "服务好、早餐丰富",
            },
        ],
        "经济": [
            {
                "name": "汉庭酒店(陆家嘴店)",
                "area": "陆家嘴",
                "price": "¥200-350",
                "rating": "4.2",
                "features": "实惠方便",
            },
            {
                "name": "如家酒店(南京路店)",
                "area": "南京路",
                "price": "¥180-300",
                "rating": "4.1",
                "features": "经济实惠",
            },
        ],
    },
    "北京": {
        "豪华": [
            {
                "name": "北京王府井文华东方酒店",
                "area": "王府井",
                "price": "¥2500-4000",
                "rating": "4.9",
                "features": "核心地段、顶级服务",
            },
            {
                "name": "北京国贸大酒店",
                "area": "国贸",
                "price": "¥2000-3000",
                "rating": "4.8",
                "features": "商务首选",
            },
            {
                "name": "北京王府半岛酒店",
                "area": "王府井",
                "price": "¥2200-3500",
                "rating": "4.8",
                "features": "奢华体验",
            },
        ],
        "舒适": [
            {
                "name": "桔子水晶酒店(王府井店)",
                "area": "王府井",
                "price": "¥500-800",
                "rating": "4.5",
                "features": "设计感强",
            },
            {
                "name": "亚朵酒店(东单店)",
                "area": "东单",
                "price": "¥450-650",
                "rating": "4.6",
                "features": "位置便利",
            },
        ],
        "经济": [
            {
                "name": "7天酒店(天安门广场店)",
                "area": "天安门",
                "price": "¥200-350",
                "rating": "4.2",
                "features": "方便看升旗",
            },
        ],
    },
    "杭州": {
        "豪华": [
            {
                "name": "西子湖四季酒店",
                "area": "西湖",
                "price": "¥2500-4000",
                "rating": "4.9",
                "features": "西湖景区、顶级享受",
            },
            {
                "name": "杭州西溪悦榕庄",
                "area": "西溪",
                "price": "¥2000-3000",
                "rating": "4.8",
                "features": "湿地景观",
            },
        ],
        "舒适": [
            {
                "name": "西子湖四季酒店(西湖店)",
                "area": "西湖",
                "price": "¥600-900",
                "rating": "4.6",
                "features": "西湖边",
            },
            {
                "name": "亚朵酒店(龙翔桥店)",
                "area": "湖滨",
                "price": "¥450-650",
                "rating": "4.5",
                "features": "地铁直达",
            },
        ],
        "经济": [
            {
                "name": "汉庭酒店(西湖店)",
                "area": "西湖",
                "price": "¥200-350",
                "rating": "4.3",
                "features": "经济实惠",
            },
        ],
    },
    "厦门": {
        "豪华": [
            {
                "name": "厦门安达仕酒店",
                "area": "环岛路",
                "price": "¥1500-2500",
                "rating": "4.8",
                "features": "海滨度假",
            },
            {
                "name": "厦门海悦山庄",
                "area": "环岛路",
                "price": "¥1200-2000",
                "rating": "4.7",
                "features": "花园式酒店",
            },
        ],
        "舒适": [
            {
                "name": "厦门海景千禧大酒店",
                "area": "轮渡",
                "price": "¥500-800",
                "rating": "4.5",
                "features": "海景房",
            },
            {
                "name": "亚呆酒店(中山路店)",
                "area": "中山路",
                "price": "¥350-500",
                "rating": "4.4",
                "features": "逛街方便",
            },
        ],
        "经济": [
            {
                "name": "曾厝垵民宿",
                "area": "曾厝垵",
                "price": "¥150-300",
                "rating": "4.3",
                "features": "特色民宿",
            },
        ],
    },
}


@tool
def recommend_hotel(city: str, budget: str = "舒适", days: int = 1) -> str:
    """
    根据目的地和预算推荐酒店或民宿。

    Args:
        city: 目标城市，如：北京、上海、杭州、厦门
        budget: 预算档次，可选：豪华、舒适、经济
        days: 预计入住天数

    Returns:
        酒店推荐信息
    """
    if not city:
        return "请提供目标城市"

    # 首先尝试使用高德 API 搜索
    amap_service = get_amap_service()
    if amap_service:
        try:
            amap_hotels = amap_service.search_hotels(city, limit=10)
            if amap_hotels:
                result = f"🏨 {city} 酒店推荐（高德地图实时数据）\n"
                result += f"{'='*50}\n\n"

                for i, hotel in enumerate(amap_hotels[:6], 1):
                    result += f"🏨 推荐 {i}: {hotel.name}\n"
                    result += f"   📍 地址: {hotel.address or '暂无'}\n"
                    result += f"   📞 电话: {hotel.tel or '暂无'}\n"
                    result += f"   🗺️ 坐标: ({hotel.location.longitude}, {hotel.location.latitude})\n"
                    result += f"   🏷️ 类型: {hotel.type}\n\n"

                result += f"{'='*50}\n"
                result += f"💡 预订建议：\n"
                result += f"   • 以上数据来自高德地图实时搜索\n"
                result += f"   • 建议通过携程/美团等平台预订\n"
                result += f"   • 入住 {days} 天建议选择连住优惠\n"

                return result
        except Exception:
            # 高德 API 调用失败，回退到本地数据库
            pass

    # 回退到本地数据库
    city_hotels = HOTEL_DATABASE.get(city, {})

    if not city_hotels:
        return f"暂不支持 {city} 的酒店推荐，请尝试其他城市"

    # 获取对应预算的酒店
    hotels = city_hotels.get(budget, [])

    if not hotels:
        # 尝试获取其他预算
        for b in ["舒适", "经济", "豪华"]:
            if b in city_hotels:
                hotels = city_hotels[b]
                budget = b
                break

    if not hotels:
        return f"暂未找到 {city} {budget} 价位的酒店信息"

    # 构建推荐结果
    result = f"🏨 {city} {budget}型酒店推荐\n"
    result += f"{'='*50}\n\n"

    for i, hotel in enumerate(hotels, 1):
        result += f"🏨 推荐 {i}: {hotel['name']}\n"
        result += f"   📍 区域: {hotel['area']}\n"
        result += f"   💰 价格: {hotel['price']}/晚\n"
        result += f"   ⭐ 评分: {hotel['rating']}\n"
        result += f"   ✨ 特色: {hotel['features']}\n"
        result += "\n"

    # 预算建议
    result += f"{'='*50}\n"
    result += f"💡 预订建议：\n"
    result += f"   • 建议提前3-7天预订，特别是周末和节假日\n"
    result += f"   • 入住 {days} 天建议选择连住优惠\n"
    result += f"   • 查看取消政策，选择免费取消的房型\n"

    # 区域建议
    area_tips = {
        "上海": "推荐外滩或陆家嘴区域，交通便利且景点集中",
        "北京": "推荐王府井或国贸区域，出行方便",
        "杭州": "推荐西湖或湖滨区域，方便游玩",
        "厦门": "推荐环岛路或中山路区域，体验更好",
    }
    if city in area_tips:
        result += f"   • {area_tips[city]}\n"

    return result


@tool
def recommend_bnb(city: str, location: str = "") -> str:
    """
    根据位置偏好推荐特色民宿。

    Args:
        city: 目标城市
        location: 偏好位置，如：海边、景区、市区

    Returns:
        民宿推荐信息
    """
    if not city:
        return "请提供目标城市"

    # 特色民宿数据库
    bnb_database = {
        "厦门": [
            {
                "name": "厦门曾厝垵海边民宿",
                "location": "海边",
                "price": "¥200-400",
                "features": "步行到海边",
            },
            {
                "name": "鼓浪屿家庭旅馆",
                "location": "景区",
                "price": "¥300-500",
                "features": "百年洋房",
            },
            {
                "name": "厦门中山路骑楼民宿",
                "location": "市区",
                "price": "¥150-300",
                "features": "老厦门味道",
            },
        ],
        "杭州": [
            {
                "name": "西湖边精品民宿",
                "location": "景区",
                "price": "¥300-600",
                "features": "步行到西湖",
            },
            {
                "name": "西溪湿地民宿",
                "location": "景区",
                "price": "¥250-500",
                "features": "湿地景观",
            },
            {
                "name": "龙井山茶园民宿",
                "location": "山区",
                "price": "¥200-400",
                "features": "茶园风光",
            },
        ],
        "大理": [
            {
                "name": "洱海海景民宿",
                "location": "海边",
                "price": "¥300-800",
                "features": "一线海景",
            },
            {
                "name": "大理古城客栈",
                "location": "市区",
                "price": "¥150-350",
                "features": "古城氛围",
            },
        ],
    }

    city_bnbs = bnb_database.get(city, [])

    if not city_bnbs:
        return f"暂未找到 {city} 的特色民宿信息"

    # 根据位置筛选
    if location:
        city_bnbs = [b for b in city_bnbs if location in b["location"]]

    if not city_bnbs:
        return f"未找到位置为 {location} 的民宿"

    result = f"🏠 {city} 特色民宿推荐\n"
    result += f"{'='*50}\n\n"

    for i, bnb in enumerate(city_bnbs, 1):
        result += f"🏠 推荐 {i}: {bnb['name']}\n"
        result += f"   📍 位置: {bnb['location']}\n"
        result += f"   💰 价格: {bnb['price']}/晚\n"
        result += f"   ✨ 特色: {bnb['features']}\n"
        result += "\n"

    result += f"{'='*50}\n"
    result += f"💡 民宿选择建议：\n"
    result += f"   • 民宿通常含早餐，特色体验好\n"
    result += f"   • 建议查看真实住客评价\n"
    result += f"   • 旺季提前2周预订\n"

    return result
