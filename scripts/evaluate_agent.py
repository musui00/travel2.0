"""
评测 Agent 系统的自动化流水线
采用 LLM-as-a-Judge 模式评估 Agent 回答质量
"""

import json
import os
import sys
import re
from typing import List, Dict, Any

import yaml
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from src.agents.main_agent import MainAgent
from src.utils.logger import logger


# 测试集定义
TEST_CASES = [
    {
        "query": "哈尔滨的最佳旅游时间是什么时候？",
        "expected_keywords": [
            "冬季",
            "12月",
            "1月",
            "2月",
            "冰雪",
            "夏天",
            "6月",
            "7月",
            "8月",
        ],
    },
    {
        "query": "哈尔滨有哪些必吃的特色美食？",
        "expected_keywords": ["红肠", "锅包肉", "杀猪菜", "铁锅炖", "烧烤", "中央大街"],
    },
    {
        "query": "从上海到哈尔滨应该怎么去？",
        "expected_keywords": ["飞机", "高铁", "火车", "上海", "哈尔滨"],
    },
    {
        "query": "哈尔滨的冰雪大世界好玩吗？值得去吗？",
        "expected_keywords": ["冰雪大世界", "冰雕", "门票", "值得", "必去"],
    },
    {
        "query": "去哈尔滨需要准备什么衣服？",
        "expected_keywords": ["羽绒服", "保暖", "手套", "帽子", "围巾", "防寒", "零下"],
    },
]

# 裁判 Prompt
JUDGE_PROMPT = """你是一个专业的旅游规划评测专家。请根据以下信息对 Agent 的回答进行评分。

## 用户问题
{query}

## 期望关键词（回答中应包含这些关键信息）
{expected_keywords}

## Agent 实际回答
{actual_response}

## 评分标准
- 5分：完美回答，准确包含所有期望关键词，信息完整且有条理
- 4分：回答良好，包含大部分期望关键词，信息较完整
- 3分：基本回答，包含部分期望关键词，但信息不够完整
- 2分：回答较差，仅包含少量期望关键词，信息不足
- 1分：回答很差，几乎没有包含期望的关键信息

## 输出要求
请严格输出 JSON 格式，不要包含任何其他内容：
{{"score": 4, "reason": "评价理由"}}
"""


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config["MODELSCOPE_API_KEY"] = os.getenv(
        "MODELSCOPE_API_KEY", config.get("MODELSCOPE_API_KEY")
    )
    return config


def init_llm(config: Dict[str, Any]) -> ChatOpenAI:
    """初始化主模型"""
    return ChatOpenAI(
        model=config["MODEL_NAME"],
        base_url=config["MODELSCOPE_BASE_URL"],
        api_key=config["MODELSCOPE_API_KEY"],
        temperature=0.7,
    )


def init_judge_llm(config: Dict[str, Any]) -> ChatOpenAI:
    """初始化裁判模型"""
    return ChatOpenAI(
        model=config["MODEL_NAME"],
        base_url=config["MODELSCOPE_BASE_URL"],
        api_key=config["MODELSCOPE_API_KEY"],
        temperature=0.3,
    )


def run_agent(agent: MainAgent, query: str) -> str:
    """运行 Agent 获取回答"""
    try:
        response = agent.run(query)
        return response
    except Exception as e:
        logger.error(f"Agent 执行失败: {e}")
        raise RuntimeError(f"Agent 请求超时或出错: {e}")


def parse_judge_response(response: str) -> Dict[str, Any]:
    """解析裁判返回的 JSON 评分"""
    try:
        # 尝试提取 JSON
        match = re.search(r"\{[^}]+\}", response, re.DOTALL)
        if match:
            result = json.loads(match.group())
            return {
                "score": int(result.get("score", 0)),
                "reason": result.get("reason", ""),
            }
        # 如果没有找到 JSON，返回默认低分
        return {"score": 0, "reason": f"无法解析裁判响应: {response[:200]}"}
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        return {"score": 0, "reason": f"JSON 解析失败: {e}"}
    except Exception as e:
        logger.error(f"裁判评分异常: {e}")
        return {"score": 0, "reason": f"裁判评分异常: {e}"}


def judge_response(
    judge_llm: ChatOpenAI,
    query: str,
    expected_keywords: List[str],
    actual_response: str,
) -> Dict[str, Any]:
    """让裁判评估回答质量"""
    prompt = JUDGE_PROMPT.format(
        query=query,
        expected_keywords=", ".join(expected_keywords),
        actual_response=actual_response,
    )

    try:
        response = judge_llm.invoke(prompt)
        return parse_judge_response(response.content)
    except Exception as e:
        logger.error(f"裁判请求失败: {e}")
        return {"score": 0, "reason": f"裁判请求失败: {e}"}


def print_report(results: List[Dict[str, Any]]) -> None:
    """打印评测报告"""
    total_score = sum(r["score"] for r in results)
    avg_score = total_score / len(results) if results else 0

    report = f"""
# Agent 评测报告

## 测试概览

| 序号 | 测试用例 | 得分 |
|:---:|:---|:---:|
"""

    for i, r in enumerate(results, 1):
        query_short = r["query"][:30] + "..." if len(r["query"]) > 30 else r["query"]
        report += f"| {i} | {query_short} | {r['score']}/5 |\n"

    report += f"""
## 统计结果

- **测试用例数**: {len(results)}
- **总分**: {total_score}/{len(results) * 5}
- **平均分**: {avg_score:.2f}/5

## 详细评价

"""

    for i, r in enumerate(results, 1):
        report += f"### Case {i}: {r['query']}\n\n"
        report += f"**得分**: {r['score']}/5\n\n"
        report += f"**评价**: {r['reason']}\n\n---\n\n"

    print(report)


def main():
    """主函数"""
    print("=" * 60)
    print("Agent 评测流水线启动")
    print("=" * 60)
    print()

    # 1. 加载配置
    logger.info("加载配置...")
    config = load_config()

    if not config.get("MODELSCOPE_API_KEY"):
        print("⚠️ 请在 .env 文件中配置 MODELSCOPE_API_KEY")
        return

    # 2. 初始化 LLM 和 Agent
    logger.info("初始化 Agent...")
    try:
        llm = init_llm(config)
        agent = MainAgent(llm)
        logger.info("Agent 初始化完成")
    except Exception as e:
        logger.error(f"Agent 初始化失败: {e}")
        print(f"⚠️ Agent 初始化失败: {e}")
        return

    # 3. 初始化裁判模型
    logger.info("初始化裁判模型...")
    try:
        judge_llm = init_judge_llm(config)
        logger.info("裁判模型初始化完成")
    except Exception as e:
        logger.error(f"裁判模型初始化失败: {e}")
        print(f"⚠️ 裁判模型初始化失败: {e}")
        return

    print()
    print("开始评测...")
    print()

    # 4. 执行评测
    results: List[Dict[str, Any]] = []

    for i, case in enumerate(TEST_CASES, 1):
        query = case["query"]
        expected_keywords = case["expected_keywords"]

        logger.info(f"Case {i}: {query}")
        print(f"[{i}/{len(TEST_CASES)}] 正在评测: {query[:40]}...")

        # 运行 Agent
        try:
            actual_response = run_agent(agent, query)
            logger.info(f"Agent 回答完成 (长度: {len(actual_response)} 字符)")
        except Exception as e:
            logger.error(f"Agent 运行失败: {e}")
            actual_response = f"Agent 运行失败: {e}"

        # 裁判评分
        try:
            judge_result = judge_response(
                judge_llm, query, expected_keywords, actual_response
            )
            logger.info(
                f"裁判评分: {judge_result['score']}/5 - {judge_result['reason'][:50]}..."
            )
        except Exception as e:
            logger.error(f"裁判评分失败: {e}")
            judge_result = {"score": 0, "reason": f"裁判评分失败: {e}"}

        results.append(
            {
                "query": query,
                "expected_keywords": expected_keywords,
                "actual_response": actual_response,
                "score": judge_result["score"],
                "reason": judge_result["reason"],
            }
        )

        print(f"  [OK] 得分: {judge_result['score']}/5")
        print()

    # 5. 输出报告
    print_report(results)

    logger.info("评测完成")


if __name__ == "__main__":
    main()
