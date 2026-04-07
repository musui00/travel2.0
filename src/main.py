"""
智能旅游规划系统 - 主入口（LangGraph Multi-Agent 版）
通过 Supervisor 模式协调多个 Sub-Agent
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
from src.agents.state import AgentState
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI


# ============================================================================
# FIX-1: 多模型 Fallback 系统（使用外部状态管理）
# ============================================================================

# 指数退避重试配置
EXPONENTIAL_BACKOFF_DELAYS = [5, 15, 30]  # 第1次5s，第2次15s，第3次30s
MAX_MODEL_RETRIES = 2  # 模型切换前的最大重试次数

# 全局模型状态（使用 dict 避免动态属性问题）
_llm_state = {
    "current_model_idx": 0,
    "consecutive_failures": 0,
    "current_model": "",
    "model_list": [],
}


def create_llm_with_fallback(config: dict):
    """创建支持多模型 fallback 的 LLM

    FIX-1: 实现多模型 Fallback 机制
    - Primary 模型连续失败2次后，自动切换到 Fallback 模型
    - 在日志中标注当前使用的模型

    Args:
        config: 配置字典

    Returns:
        LLM 实例
    """
    global _llm_state

    # 获取模型列表
    model_list = [config["MODEL_NAME"]] + config.get("MODEL_FALLBACK_LIST", [])

    # 初始化全局状态
    _llm_state["model_list"] = model_list
    _llm_state["current_model_idx"] = 0
    _llm_state["consecutive_failures"] = 0
    _llm_state["current_model"] = model_list[0]

    # 创建 LLM 实例
    llm = ChatOpenAI(
        model=model_list[0],
        base_url=config["MODELSCOPE_BASE_URL"],
        api_key=config["MODELSCOPE_API_KEY"],
        temperature=0.7,
        max_retries=2,
        request_timeout=60,
    )

    logger.info(f"[LLM] 初始化完成，使用模型: {model_list[0]}")
    print(f"[LLM] ✅ 当前使用模型: {model_list[0]}")

    return llm


def switch_to_next_model(config: dict) -> ChatOpenAI | None:
    """切换到下一个模型

    FIX-1: 模型失败时调用此函数切换

    Args:
        config: 配置字典

    Returns:
        新的 LLM 实例，如果所有模型都失败则返回 None
    """
    global _llm_state

    _llm_state["current_model_idx"] += 1

    if _llm_state["current_model_idx"] < len(_llm_state["model_list"]):
        new_model = _llm_state["model_list"][_llm_state["current_model_idx"]]
        _llm_state["current_model"] = new_model
        _llm_state["consecutive_failures"] = 0  # 重置失败计数

        logger.warning(f"[LLM] 切换到备选模型: {new_model}")
        print(f"[LLM] 🔄 切换到备选模型: {new_model}")

        return ChatOpenAI(
            model=new_model,
            base_url=config["MODELSCOPE_BASE_URL"],
            api_key=config["MODELSCOPE_API_KEY"],
            temperature=0.7,
            max_retries=2,
            request_timeout=60,
        )
    else:
        logger.error("[LLM] 所有模型均已失败")
        print(f"[LLM] ⚠️ 所有模型均已失败")
        return None


def get_current_model() -> str:
    """获取当前使用的模型名称"""
    return _llm_state["current_model"]


def record_failure():
    """记录一次失败，用于触发模型切换"""
    global _llm_state
    _llm_state["consecutive_failures"] += 1


def should_switch_model() -> bool:
    """判断是否应该切换模型"""
    return _llm_state["consecutive_failures"] >= MAX_MODEL_RETRIES


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
    # 尝试 URL 方式加载图片（更稳定）
    # 如果是本地文件，转换为 data URL
    try:
        # 读取图片并转为 base64
        import base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{image_data}"
    except Exception:
        # 如果读取失败，使用默认路径
        image_url = image_path

    prompt = """你是一个专业的图像识别助手。请仔细分析用户提供的图片，识别图片中的场景类型。

请从以下类型中选择最匹配的一个：
- 海滩（沙滩、海滨、海岸）
- 湖泊（湖边、湖畔、湖光）
- 公园（园林、植物园、花园）
- 山景（山峰、峡谷）
- 古镇（老街、历史街区）
- 寺庙（古刹、禅寺、教堂）
- 游乐场（主题公园、动物园）

请用简洁的语言描述图片中的场景，并给出场景类型。格式如下：
场景描述：xxx
场景类型：xxx（如：海滩、湖泊、公园等）

请用中文回复。"""

    # 构建消息 - 使用简化的内容格式
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请分析这张图片，识别场景类型。"},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
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


def main():
    """主函数 - 使用 LangGraph Multi-Agent 架构"""
    print("=" * 60)
    print("欢迎使用智能旅游规划系统 (LangGraph Multi-Agent 版)")
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

    # 3. 获取旅游日期
    print("\n【步骤3】请输入期望的旅游日期：")
    print("示例：4.6到4.8 或 2024-04-06 至 2024-04-08")
    travel_dates = input("旅游日期: ").strip()

    # 4. 获取现处位置
    print("\n【步骤4】请输入您当前所在城市：")
    print("示例：上海、深圳、广州")
    from_city = input("现处城市: ").strip()

    print("\n" + "=" * 60)
    print("正在通过 LangGraph Multi-Agent 智能生成旅游规划...")
    print("(Supervisor 将协调 Transport/Accommodation/Food/Sightseeing Agent)")
    print("=" * 60)

    # 4. 初始化 LLM 和 LangGraph
    try:
        # FIX-1: 使用多模型 Fallback 系统
        llm = create_llm_with_fallback(config)

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

        # 6. 构建用户请求（包含日期信息，供天气和航班使用）
        user_request = f"""我想去 {target_city} 旅游，现居住在 {from_city}。
旅行日期：{travel_dates}
出发日期：{travel_dates}

根据我上传的图片，识别到的场景类型是：{scene_type}

请帮我生成一份完整的旅游规划，包括：
1. 推荐适合 {scene_type} 类型的景点（使用本地知识库检索详细攻略）
2. 查询 {target_city} 在 {travel_dates} 期间的天气情况
3. 从 {from_city} 到 {target_city} 的航班/交通信息
4. {target_city} 的住宿推荐
5. {target_city} ��美��推荐

注意：
- 天气和交通信息必须实时查询（不使用本地数据库）
- 景点推荐可以使用本地知识库（RAG）
- 请用中文回复，结构清晰地展示各部分内容"""

        # 7. 尝试使用 LangGraph（如果已安装 langgraph）
        use_langgraph = False
        try:
            from src.agents.graph import create_travel_planner

            print("\n正在初始化 LangGraph Multi-Agent...")
            app = create_travel_planner(llm)
            use_langgraph = True
        except ImportError as e:
            print(f"⚠️ LangGraph 未安装: {e}")
            print("将回退到单 Agent 模式")
            use_langgraph = False

        if use_langgraph:
            # 使用 LangGraph 工作流
            print("\n" + "-" * 40)
            print("【LangGraph Multi-Agent 规划中...】")
            print("-" * 40)

            # 初始化状态 - 使用 "FINISH" 让 Supervisor 做出初始路由决策
            initial_state: AgentState = {
                "messages": [HumanMessage(content=user_request)],
                "next_agent": "FINISH",  # 触发 Supervisor 首次决策
                "travel_plan": {},
                "visited_agents": set(),  # FIX: 初始化已访问 Agent 集合
                "iteration_count": 0,  # FIX: 初始化迭代计数器
            }

            # 执行工作流
            try:
                result = app.invoke(initial_state)

                # 调试：打印完整结果
                print(f"[DEBUG] LangGraph 结果: {result}")

                final_plan = result.get("travel_plan", {})

                print("\n" + "=" * 60)
                print("【旅游规划结果】")
                print("=" * 60)

                # 按顺序展示各 Agent 的结果
                for agent_name, content in final_plan.items():
                    if content:
                        print(f"\n### {agent_name.upper()} ###\n")
                        print(content[:500] if len(content) > 500 else content)
                        print()

            except Exception as e:
                logger.error(f"LangGraph 执行失败: {e}")
                import traceback
                traceback.print_exc()
                print(f"⚠️ 执行失败: {e}")
                use_langgraph = False

        if not use_langgraph:
            # 回退到原来的单 Agent 模式
            print("\n使用单 Agent 模式...")
            from src.agents.main_agent import MainAgent

            agent = MainAgent(llm)
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