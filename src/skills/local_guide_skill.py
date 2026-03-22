"""
本地知识库检索 Skill
基于 RAG (Retrieval Augmented Generation) 方式查询本地旅游攻略文档
使用 LangChain Tool 格式
"""

from pydantic import BaseModel, Field

from langchain_core.tools import tool

from src.utils.logger import logger
from src.utils.rag_manager import RAGManager


class LocalGuideInput(BaseModel):
    """本地知识库查询输入模型"""

    query: str = Field(
        description="查询字符串，例如：'哈尔滨有哪些特色美食'、'中央大街附近有什么景点推荐'"
    )


# RAG 管理器实例（延迟初始化）
_rag_manager: RAGManager | None = None


def _get_rag_manager() -> RAGManager:
    """获取或创建 RAG 管理器实例"""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGManager()
    return _rag_manager


@tool
def search_local_guide(query: str) -> str:
    """
    当用户询问关于某城市的特色景点、小众路线、本地美食或具体的旅游攻略详情时，
    必须调用此工具检索本地知识库。

    Args:
        query: 查询字符串，例如：'哈尔滨有哪些特色美食'、'中央大街附近有什么景点推荐'

    Returns:
        从本地知识库检索到的相关内容，如果检索失败返回友好提示
    """
    if not query or not query.strip():
        return "请提供有效的查询内容"

    try:
        logger.info(f"本地知识库检索: {query}")
        rag = _get_rag_manager()
        result = rag.query(query)
        logger.info("本地知识库检索成功")
        return result

    except FileNotFoundError as e:
        logger.warning(f"本地知识库文件未找到: {e}")
        return (
            "抱歉，本地知识库暂时不可用。"
            "请检查 data/我是驴友-哈尔滨旅游攻略.pdf 文件是否存在。"
        )

    except Exception as e:
        logger.error(f"本地知识库检索失败: {e}")
        return (
            "抱歉，检索本地知识库时发生错误。"
            "请稍后再试或换个问题。"
        )
