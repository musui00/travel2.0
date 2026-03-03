"""
智能旅游规划系统 - 主入口
采用 LangChain Agent 架构，支持图片理解、景点推荐、旅游规划等功能
"""

import os
import sys
import base64
import yaml
from langchain_openai import ChatOpenAI

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.main_agent import MainAgent


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def encode_image(image_path: str) -> str:
    """将图片转换为base64编码"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_image(llm: ChatOpenAI, image_path: str) -> str:
    """分析图片，理解内容"""
    base64_image = encode_image(image_path)

    prompt = """你是一个专业的图像识别助手。请仔细分析用户提供的图片，描述图片中的内容、场景和特点。

请用简洁、生动的语言描述图片，包括：
- 图片中的主要景物或场景
- 可能的地点特征
- 画面整体氛围和风格

请用中文回复。"""

    # 构建消息
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请分析这张图片，描述图片中的内容。"},
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


def main():
    """主函数"""
    print("=" * 60)
    print("欢迎使用智能旅游规划系统 (LangChain版)")
    print("=" * 60)

    # 加载配置
    config = load_config()

    # 初始化 LangChain LLM
    llm = ChatOpenAI(
        model=config["MODEL_NAME"],
        base_url=config["MODELSCOPE_BASE_URL"],
        api_key=config["MODELSCOPE_API_KEY"],
        temperature=0.7,
    )

    # 获取用户输入
    print("\n请输入图片路径：")
    image_path = input().strip()

    if not os.path.exists(image_path):
        print(f"错误：图片文件不存在: {image_path}")
        return

    # 阶段1：理解图片
    print("\n" + "=" * 60)
    print("【图片理解】分析图片内容...")
    print("=" * 60)

    image_analysis = analyze_image(llm, image_path)
    print(image_analysis)
    print()

    # 阶段2：LangChain Agent 处理
    print("\n" + "=" * 60)
    print("【LangChain Agent】开始生成旅游规划...")
    print("=" * 60)

    main_agent = MainAgent(llm)
    user_requirement = input("请输入您的旅游需求（如：我要去这里玩3天）：")

    final_plan = main_agent.run(user_requirement, image_analysis)

    # 输出最终规划
    print("\n" + "=" * 60)
    print("【最终旅游规划】")
    print("=" * 60)
    print(final_plan)

    print("\n" + "=" * 60)
    print("规划完成！祝您旅途愉快！")
    print("=" * 60)


if __name__ == "__main__":
    main()
