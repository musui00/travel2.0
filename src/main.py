"""
智能旅游规划系统 - 主入口
根据图片推荐相似景点 + 天气查询 + 交通推荐
"""

import os
import sys
import base64
import yaml
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

from src.skills import test_tool
from src.utils.logger import logger


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 环境变量优先级高于配置文件
    config["MODELSCOPE_API_KEY"] = os.getenv(
        "MODELSCOPE_API_KEY", config.get("MODELSCOPE_API_KEY")
    )
    config["WEATHER_API_KEY"] = os.getenv(
        "WEATHER_API_KEY", config.get("WEATHER_API_KEY")
    )
    config["FLIGHT_API_KEY"] = os.getenv("FLIGHT_API_KEY", config.get("FLIGHT_API_KEY"))

    return config


def encode_image(image_path: str) -> str:
    """将图片转换为base64编码"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_image_scene(llm, image_path: str) -> str:
    """分析图片，识别场景类型（海边、公园、湖畔等）"""
    base64_image = encode_image(image_path)

    prompt = """你是一个专业的图像识别助手。请仔细分析用户提供的图片，识别图片中的场景类型。

请从以下类型中选择最匹配的一个或多个：
- 海滩（沙滩、海滨、海岸）
- 湖泊（湖边、湖畔、湖光）
- 公园（园林、植物园、花园）
- 山景（山峰、峡谷）
- 古镇（老街、历史街区）
- 寺庙（古刹、禅寺）
- 游乐场（主题公园、动物园）

请用简洁的语言描述图片中的场景，并给出场景类型。格式如下：
场景描述：xxx
场景类型：xxx（如：海滩、湖泊、公园等）

请用中文回复。"""

    # 构建消息
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请分析这张图片，识别场景类型。"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        },
    ]

    # 调用模型
    response = llm.invoke(messages)
    return response.content


def extract_scene_type(analysis_result: str) -> str:
    """从分析结果中提取场景类型"""
    # 常见场景类型关键词
    scene_keywords = {
        "海滩": ["海滩", "沙滩", "海滨", "海岸", "海湾", "海洋"],
        "湖泊": ["湖", "湿地", "水库"],
        "公园": ["公园", "园林", "植物园", "花园", "广场"],
        "山景": ["山", "峰", "峡谷", "森林", "林"],
        "古镇": ["古镇", "古城", "老街", "胡同", "村落"],
        "寺庙": ["寺庙", "古刹", "禅寺", "教堂", "塔"],
        "游乐": ["游乐场", "主题公园", "动物园", "海洋馆"],
    }

    analysis_lower = analysis_result.lower()

    for scene_type, keywords in scene_keywords.items():
        for keyword in keywords:
            if keyword in analysis_lower:
                return scene_type

    # 默认返回公园
    return "公园"


def recommend_transport(from_city: str, to_city: str) -> str:
    """推荐交通工具"""
    # 判断是否是同城
    is_same_city = from_city == to_city

    if is_same_city:
        result = f"📍 {from_city}市内交通推荐：\n\n"
        result += f"{'='*50}\n\n"

        # 当地交通
        result += "🚇 公共交通：\n"
        result += f"   • 地铁：{from_city}地铁网络发达，建议优先选择\n"
        result += f"   • 公交：票价实惠，线路覆盖广\n"
        result += f"   • 建议使用地图APP规划路线\n\n"

        result += "🚗 打车/租车：\n"
        result += f"   • 滴滴出行/T3出行：方便快捷\n"
        result += f"   • 出租车：可用APP叫车或路边拦车\n"
        result += f"   • 共享单车：适合短途出行\n\n"

        result += "🗺️ 出行建议：\n"
        result += f"   • 建议使用高德/百度地图APP导航\n"
        result += f"   • 早高峰(7-9点)建议提前出行\n"
        result += f"   • 景区周边停车不便，建议公共交通\n"

        return result

    # 跨城交通
    result = f"🚄 从 {from_city} 到 {to_city} 的交通方式：\n\n"
    result += f"{'='*50}\n\n"

    # 航班
    try:
        flight_result = test_tool(
            "flight_search", {"from_city": from_city, "to_city": to_city}
        )
        result += "✈️ 航班信息：\n"
        # 取前2个航班
        lines = flight_result.split("\n")
        for line in lines[:10]:
            if line.strip():
                result += "   " + line + "\n"
        result += "\n"
    except Exception as e:
        logger.error(f"航班查询失败: {e}")
        result += "   航班查询暂不可用\n\n"

    # 高铁
    result += "🚄 高铁/火车建议：\n"
    result += "   • 建议乘坐高铁，舒适快捷\n"
    result += "   • 提前在12306官网/APP预订车票\n"
    result += "   • 高铁站通常位于市中心附近，交通便利\n\n"

    # 当地交通
    result += "🚗 到达后市内交通：\n"
    result += "   • 地铁+公交组合：经济实惠\n"
    result += "   • 滴滴打车/出租车：方便快捷\n"
    result += "   • 共享单车：适合短途游览\n"

    return result


def main():
    """主函数 - 使用 MainAgent 智能处理用户请求"""
    print("=" * 60)
    print("欢迎使用智能旅游规划系统 (RAG增强版)")
    print("=" * 60)
    print()

    # 加载配置
    config = load_config()

    # 检查 API Key
    if (
        not config.get("MODELSCOPE_API_KEY")
        or config.get("MODELSCOPE_API_KEY") == "your_modelScope_api_key_here"
    ):
        print("⚠️ 请在 .env 文件中配置 MODELSCOPE_API_KEY")
        print("或者直接使用离线模式（跳过图片分析）")
        use_offline = input("是否使用离线模式？(y/n): ").strip().lower()
        if use_offline != "y":
            return

    # 1. 获取图片路径
    print("\n【步骤1】请输入图片路径（您想去的地方的图片）：")
    print("示例：images/beach.jpg")
    image_path = input("图片路径: ").strip()

    # 2. 获取目标城市
    print("\n【步骤2】请输入目标城市：")
    print("示例：厦门、杭州、哈尔滨")
    target_city = input("目标城市: ").strip()

    # 3. 获取现处位置
    print("\n【步骤3】请输入您当前所在城市：")
    print("示例：上海、深圳、广州")
    from_city = input("现处城市: ").strip()

    print("\n" + "=" * 60)
    print("正在通过 MainAgent 智能生成旅游规划...")
    print("(大模型将自动决定何时调用 RAG 检索本地知识库)")
    print("=" * 60)

    # 4. 初始化 LLM 和 MainAgent
    try:
        from langchain_openai import ChatOpenAI
        from src.agents.main_agent import MainAgent

        llm = ChatOpenAI(
            model=config["MODEL_NAME"],
            base_url=config["MODELSCOPE_BASE_URL"],
            api_key=config["MODELSCOPE_API_KEY"],
            temperature=0.7,
        )

        # 创建 MainAgent（会自动加载所有 Tools 包括 search_local_guide）
        agent = MainAgent(llm)

        # 5. 图片分析 - 识别场景类型
        scene_type = None
        image_analysis = ""

        if os.path.exists(image_path):
            print("\n正在分析图片...")
            try:
                image_analysis = analyze_image_scene(llm, image_path)
                print(f"图片分析结果: {image_analysis}")
                scene_type = extract_scene_type(image_analysis)
                print(f"识别场景类型: {scene_type}")
            except Exception as e:
                logger.error(f"图片分析失败: {e}")
                print(f"⚠️ 图片分析失败: {e}")
                scene_type = "公园"
        else:
            print(f"⚠️ 图片文件不存在: {image_path}")
            scene_type = "公园"

        # 6. 构建用户请求，交给 MainAgent 处理
        user_request = f"""我想去 {target_city} 旅游，现居住在 {from_city}。

根据我上传的图片，识别到的场景类型是：{scene_type}

请帮我生成一份完整的旅游规划，包括：
1. 推荐适合 {scene_type} 类型的景点
2. 查询 {target_city} 的天气情况
3. 从 {from_city} 到 {target_city} 的交通方式
4. {target_city} 的住宿推荐
5. {target_city} 的美食推荐
6. 如果有本地知识库，请检索 {target_city} 的详细旅游攻略"""

        # 7. MainAgent 自动处理（会调用 RAG 等工具）
        print("\n" + "-" * 40)
        print("【AI 智能规划中...】")
        print("-" * 40)
        result = agent.run(user_request, image_analysis=image_analysis)

        print("\n" + "=" * 60)
        print("【旅游规划结果】")
        print("=" * 60)
        print(result)

    except Exception as e:
        logger.error(f"MainAgent 执行失败: {e}")
        print(f"⚠️ AI 处理失败: {e}")
        print("请检查 API Key 是否正确")

    print("\n" + "=" * 60)
    print("规划完成！祝您旅途愉快！")
    print("=" * 60)


if __name__ == "__main__":
    main()
