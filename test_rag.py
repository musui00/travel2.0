"""单独测试 RAG 能力"""

from src.utils.rag_manager import RAGManager
from src.utils.logger import logger


def test_rag() -> None:
    """测试本地知识库检索"""
    logger.info("=" * 50)
    logger.info("测试 RAG 本地知识库检索")
    logger.info("=" * 50)

    # 创建 RAG 管理器
    rag = RAGManager(markdown_path="data_markdown/哈尔滨旅游攻略.md")

    # 加载 Markdown 并创建向量库（首次运行）
    logger.info("[1] 加载 Markdown 并创建向量库...")
    try:
        rag.load_and_index()
        logger.info("向量库创建成功")
    except FileNotFoundError as e:
        logger.error(f"Markdown 文件不存在: {e}")
        return
    except Exception as e:
        logger.error(f"加载失败: {e}")
        return

    # 测试查询
    test_questions = [
        "哈尔滨有哪些特色美食？",
        "中央大街附近有什么景点？",
        "去哈尔滨旅游的最佳时间是什么时候？",
    ]

    logger.info("[2] 开始查询测试...")
    logger.info("-" * 50)

    for question in test_questions:
        logger.info(f"\n问题: {question}")
        logger.info("-" * 30)
        result = rag.query(question)
        logger.info(result[:500] if len(result) > 500 else result)
        logger.info("")


if __name__ == "__main__":
    test_rag()
