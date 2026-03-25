"""
餐饮推荐 Skill
根据城市和菜系推荐餐厅、小吃
使用 LangChain Tool 格式
"""

from typing import Dict, List
from langchain_core.tools import tool

# 美食数据库
FOOD_DATABASE = {
    "上海": {
        "本帮菜": [
            {
                "name": "上海老饭店",
                "area": "城隍庙",
                "price": "¥80-150",
                "rating": "4.6",
                "dish": "红烧肉、八宝鸭",
            },
            {
                "name": "绿波廊",
                "area": "城隍庙",
                "price": "¥70-120",
                "rating": "4.5",
                "dish": "蟹粉小笼、桂花糕",
            },
            {
                "name": "南翔小笼",
                "area": "城隍庙",
                "price": "¥30-60",
                "rating": "4.7",
                "dish": "小笼包、馄饨",
            },
        ],
        "海派菜": [
            {
                "name": "老吉士酒家",
                "area": "天平路",
                "price": "¥100-200",
                "rating": "4.6",
                "dish": "吉士红烧肉",
            },
            {
                "name": "福1039",
                "area": "江苏路",
                "price": "¥150-300",
                "rating": "4.8",
                "dish": "创意本帮菜",
            },
        ],
        "小吃": [
            {
                "name": "阿大葱油饼",
                "area": "茂名南路",
                "price": "¥5-10",
                "rating": "4.5",
                "dish": "葱油饼",
            },
            {
                "name": "王家沙点心店",
                "area": "南京西路",
                "price": "¥20-50",
                "rating": "4.4",
                "dish": "蟹粉汤圆",
            },
        ],
    },
    "北京": {
        "京菜": [
            {
                "name": "全聚德(和平门店)",
                "area": "前门",
                "price": "¥150-300",
                "rating": "4.5",
                "dish": "烤鸭",
            },
            {
                "name": "便宜坊(鲜鱼口店)",
                "area": "前门",
                "price": "¥120-250",
                "rating": "4.6",
                "dish": "焖炉烤鸭",
            },
            {
                "name": "东来顺(王府井店)",
                "area": "王府井",
                "price": "¥100-200",
                "rating": "4.4",
                "dish": "涮羊肉",
            },
        ],
        "小吃": [
            {
                "name": "护国寺小吃店",
                "area": "护国寺",
                "price": "¥20-50",
                "rating": "4.3",
                "dish": "豆汁、艾窝窝",
            },
            {
                "name": "锦芳小吃(崇文门店)",
                "area": "崇文门",
                "price": "¥20-50",
                "rating": "4.4",
                "dish": "元宵、驴打滚",
            },
        ],
    },
    "杭州": {
        "杭帮菜": [
            {
                "name": "楼外楼(孤山店)",
                "area": "西湖",
                "price": "¥100-200",
                "rating": "4.5",
                "dish": "西湖醋鱼、东坡肉",
            },
            {
                "name": "外婆家(西湖银泰店)",
                "area": "西湖",
                "price": "¥50-100",
                "rating": "4.4",
                "dish": "茶香鸡",
            },
            {
                "name": "知味观(仁和路店)",
                "area": "湖滨",
                "price": "¥80-150",
                "rating": "4.6",
                "dish": "猫耳朵、片儿川",
            },
        ],
        "小吃": [
            {
                "name": "新丰小吃(解放路店)",
                "area": "湖滨",
                "price": "¥15-40",
                "rating": "4.3",
                "dish": "小笼包、牛肉粉丝",
            },
        ],
    },
    "厦门": {
        "闽南菜": [
            {
                "name": "厦门佳丽海鲜大排档",
                "area": "环岛路",
                "price": "¥80-150",
                "rating": "4.5",
                "dish": "海鲜、姜母鸭",
            },
            {
                "name": "1980烧肉粽",
                "area": "中山路",
                "price": "¥20-50",
                "rating": "4.4",
                "dish": "烧肉粽",
            },
            {
                "name": "黄则和花生汤店",
                "area": "中山路",
                "price": "¥15-40",
                "rating": "4.3",
                "dish": "花生汤、沙茶面",
            },
        ],
        "小吃": [
            {
                "name": "沙茶面",
                "area": "鼓浪屿",
                "price": "¥20-40",
                "rating": "4.5",
                "dish": "沙茶面",
            },
            {
                "name": "海蛎煎",
                "area": "曾厝垵",
                "price": "¥15-30",
                "rating": "4.4",
                "dish": "海蛎煎",
            },
        ],
    },
    "成都": {
        "川菜": [
            {
                "name": "麻婆豆腐(春熙路店)",
                "area": "春熙路",
                "price": "¥50-100",
                "rating": "4.6",
                "dish": "麻婆豆腐",
            },
            {
                "name": "巴蜀大宅门火锅",
                "area": "玉林",
                "price": "¥80-150",
                "rating": "4.7",
                "dish": "川味火锅",
            },
            {
                "name": "老成都川菜馆",
                "area": "宽窄巷子",
                "price": "¥60-120",
                "rating": "4.5",
                "dish": "水煮鱼",
            },
        ],
        "小吃": [
            {
                "name": "龙抄手(春熙路店)",
                "area": "春熙路",
                "price": "¥15-40",
                "rating": "4.4",
                "dish": "红油抄手",
            },
            {
                "name": "三大炮(锦里)",
                "area": "锦里",
                "price": "¥10-30",
                "rating": "4.3",
                "dish": "三大炮",
            },
        ],
    },
    "西安": {
        "西北菜": [
            {
                "name": "西安饭庄(东大街店)",
                "area": "东大街",
                "price": "¥60-120",
                "rating": "4.5",
                "dish": "羊肉泡馍",
            },
            {
                "name": "老孙家泡馍",
                "area": "东大街",
                "price": "¥40-80",
                "rating": "4.4",
                "dish": "泡馍",
            },
            {
                "name": "同盛祥(钟楼店)",
                "area": "钟楼",
                "price": "¥40-80",
                "rating": "4.5",
                "dish": "牛羊肉泡馍",
            },
        ],
        "小吃": [
            {
                "name": "回民街",
                "area": "北院门",
                "price": "¥20-50",
                "rating": "4.6",
                "dish": "肉夹馍、凉皮",
            },
            {
                "name": "樊记腊汁肉夹馍",
                "area": "回民街",
                "price": "¥10-25",
                "rating": "4.5",
                "dish": "肉夹馍",
            },
        ],
    },
}


@tool
def recommend_restaurant(city: str, cuisine: str = "", price_level: str = "") -> str:
    """
    根据城市和菜系推荐餐厅。

    Args:
        city: 目标城市，如：北京、上海、杭州、厦门
        cuisine: 菜系类型，如：本帮菜、川菜、火锅等（可选）
        price_level: 价位，可选：经济、舒适、豪华（可选）

    Returns:
        餐厅推荐信息
    """
    if not city:
        return "请提供目标城市"

    # 获取城市美食数据
    city_foods = FOOD_DATABASE.get(city, {})

    if not city_foods:
        return f"暂不支持 {city} 的餐厅推荐"

    # 筛选菜系
    if cuisine:
        # 模糊匹配菜系
        matched_cuisines = [k for k in city_foods.keys() if cuisine in k]
        if matched_cuisines:
            cuisines = matched_cuisines
        else:
            cuisines = list(city_foods.keys())[:1]
    else:
        cuisines = list(city_foods.keys())[:2]

    if not cuisines:
        return f"暂未找到 {city} {cuisine} 类型餐厅"

    result = f"🍽️ {city} 餐厅推荐\n"
    result += f"{'='*50}\n\n"

    for cuisine_type in cuisines:
        restaurants = city_foods.get(cuisine_type, [])
        if not restaurants:
            continue

        result += f"📌 {cuisine_type}\n"
        result += f"{'-'*40}\n"

        for i, restaurant in enumerate(restaurants[:3], 1):
            result += f"   {i}. {restaurant['name']}\n"
            result += f"      📍 位置: {restaurant['area']}\n"
            result += f"      💰 人均: {restaurant['price']}\n"
            result += f"      ⭐ 评分: {restaurant['rating']}\n"
            result += f"      🍜 招牌: {restaurant['dish']}\n\n"

    # 推荐理由
    result += f"{'='*50}\n"
    result += f"💡 美食推荐理由：\n"
    result += f"   • 以上餐厅均为当地口碑店铺\n"
    result += f"   • 建议提前预约，避免排队\n"
    result += f"   • 可通过大众点评查看实时排队情况\n"

    return result


@tool
def recommend_snacks(city: str) -> str:
    """
    推荐城市特色小吃。

    Args:
        city: 目标城市

    Returns:
        小吃推荐信息
    """
    if not city:
        return "请提供目标城市"

    # 小吃推荐（使用餐厅数据库中的小吃）
    city_foods = FOOD_DATABASE.get(city, {})
    snacks_data = city_foods.get("小吃", [])

    if not snacks_data:
        # 尝试获取其他类别中的小吃
        for cuisine, restaurants in city_foods.items():
            for r in restaurants:
                if (
                    "小笼" in r.get("dish", "")
                    or "抄手" in r.get("dish", "")
                    or "包子" in r.get("dish", "")
                ):
                    snacks_data.append(r)

    if not snacks_data:
        return f"暂未找到 {city} 的特色小吃信息"

    result = f"🍜 {city} 特色小吃推荐\n"
    result += f"{'='*50}\n\n"

    for i, snack in enumerate(snacks_data[:5], 1):
        result += f"{i}. {snack['name']}\n"
        result += f"   📍 位置: {snack['area']}\n"
        result += f"   💰 价格: {snack['price']}\n"
        result += f"   ⭐ 必吃: {snack['dish']}\n\n"

    result += f"{'='*50}\n"
    result += f"💡 小吃打卡建议：\n"
    result += f"   • 小吃一般在老城区或美食街最为正宗\n"
    result += f"   • 建议中午或下午去，晚上很多店会关门\n"
    result += f"   • 跟着本地人排队的地方味道通常不错\n"

    return result
