"""RAG Manager for local knowledge base retrieval using structured Markdown."""

import re
from pathlib import Path
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from src.utils.logger import logger

# 定义 Markdown 标题层级
HEADERS_TO_SPLIT_ON = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]


def clean_text(text: str) -> str:
    """清洗 Markdown 文本，去除图片、多余空白."""
    # 删除所有 Markdown 图片标签 ![...](...)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # 将连续3个及以上换行替换为2个换行
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 移除控制字符
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    # 移除行首行尾空白
    text = text.strip()
    return text


class RAGManager:
    """Manages Markdown document loading, embedding, and retrieval.

    Uses MarkdownHeaderTextSplitter for structural retrieval:
    - First split by headers (# ## ###) to preserve document structure
    - Then split with RecursiveCharacterTextSplitter as safety net
    - Stores in chroma_db_md directory
    """

    def __init__(
        self,
        markdown_path: str = "data_markdown/guide_structured.md",
        persist_directory: str = "./chroma_db_md",
        embedding_model: str = "moka-ai/m3e-base",
    ) -> None:
        """Initialize the RAG Manager.

        Args:
            markdown_path: Path to the Markdown document.
            persist_directory: Directory to persist the vector database.
            embedding_model: HuggingFace embedding model name.
        """
        self.markdown_path = markdown_path
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": "cpu"},
        )

        # 按标题层级切分
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=HEADERS_TO_SPLIT_ON,
        )

        # 二次切分：防止单块过长
        self.backup_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"],
        )

        # 向量存储
        self.vectorstore: Chroma | None = None

    def _load_markdown(self) -> tuple[str, str]:
        """加载 Markdown 文件.

        Returns:
            元组 (原始内容, 清洗后的内容).
        """
        markdown_file = Path(self.markdown_path)

        if not markdown_file.exists():
            logger.error(f"Markdown file not found: {self.markdown_path}")
            raise FileNotFoundError(
                f"Markdown file not found: {self.markdown_path}. "
                "Please place the Markdown file in the data_markdown directory."
            )

        try:
            logger.info(f"Loading Markdown from: {self.markdown_path}")
            content = markdown_file.read_text(encoding="utf-8")
            cleaned_content = clean_text(content)
            logger.info(
                f"Loaded Markdown file ({len(cleaned_content)} chars after cleaning)"
            )
            return content, cleaned_content
        except Exception as e:
            logger.error(f"Failed to load Markdown: {e}")
            raise

    def _init_vectorstore(self) -> Chroma:
        """初始化或加载 Chroma 向量库.

        Returns:
            Chroma 向量库实例.
        """
        persist_path = Path(self.persist_directory)

        if persist_path.exists():
            try:
                logger.info(
                    f"Loading existing vector store from: {self.persist_directory}"
                )
                vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                )
                if vectorstore._collection.count() > 0:
                    logger.info(
                        f"Loaded existing vector store with {vectorstore._collection.count()} chunks"
                    )
                    return vectorstore
                else:
                    logger.info("Existing vector store is empty, recreating...")
            except Exception as e:
                logger.warning(
                    f"Failed to load existing vector store: {e}, recreating..."
                )

        logger.info(f"Creating new vector store at: {self.persist_directory}")
        vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )
        return vectorstore

    def load_and_index(self) -> None:
        """加载 Markdown 并创建向量库."""
        try:
            # Step 1: 加载 Markdown（获取原始和清洗后的内容）
            _, cleaned_content = self._load_markdown()

            # Step 2: 按标题层级切分（保留 metadata）
            logger.info("Splitting by Markdown headers...")
            header_docs = self.header_splitter.split_text(cleaned_content)
            logger.info(f"Created {len(header_docs)} header-based chunks")

            # Step 3: 二次切分（防止单块过长）
            logger.info("Applying backup splitter (chunk_size=300, overlap=50)...")
            final_docs: List[Document] = []

            for doc in header_docs:
                # 如果文档长度超过 300，进行二次切分
                if len(doc.page_content) > 300:
                    sub_docs = self.backup_splitter.split_documents([doc])
                    # 保留原始 metadata（标题信息）
                    for sub_doc in sub_docs:
                        sub_doc.metadata.update(doc.metadata)
                    final_docs.extend(sub_docs)
                else:
                    final_docs.append(doc)

            logger.info(f"Created {len(final_docs)} chunks after backup splitting")

            # 过滤空文档
            final_docs = [doc for doc in final_docs if doc.page_content.strip()]
            logger.info(f"After filtering empty docs: {len(final_docs)} chunks")

            if not final_docs:
                raise ValueError("No valid documents to index")

            # Step 4: 初始化向量库
            self.vectorstore = self._init_vectorstore()

            # Step 5: 清空并重新填充
            logger.info("Adding chunks to vector store...")
            self.vectorstore.delete_collection()
            self.vectorstore = Chroma.from_documents(
                documents=final_docs,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
            )

            logger.info("Markdown RAG initialized and persisted successfully")

        except Exception as e:
            logger.error(f"Failed to load and index Markdown: {e}")
            raise

    def load_existing(self) -> None:
        """加载已存在的向量库."""
        persist_path = Path(self.persist_directory)

        if not persist_path.exists():
            logger.error(f"Vector store not found at: {self.persist_directory}")
            raise FileNotFoundError(
                f"Vector store not found at: {self.persist_directory}. "
                "Please run load_and_index() first."
            )

        try:
            logger.info(f"Loading existing vector store from: {self.persist_directory}")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )

            count = self.vectorstore._collection.count()
            logger.info(f"Loaded vector store with {count} chunks")

        except Exception as e:
            logger.error(f"Failed to load existing vector store: {e}")
            raise

    def query(self, question: str, k: int = 3) -> str:
        """查询向量库，返回相关内容.

        Args:
            question: 查询字符串.
            k: 返回结果数量.

        Returns:
            格式化字符串，包含 page_content 和 metadata（章节标题）.
        """
        if self.vectorstore is None:
            try:
                self.load_existing()
            except FileNotFoundError:
                logger.info("No existing vector store found, creating new one...")
                self.load_and_index()

        try:
            logger.info(f"Querying: {question}")

            results = self.vectorstore.similarity_search(question, k=k)

            if not results:
                logger.warning("No relevant documents found")
                return "未找到相关内容"

            logger.info(f"Found {len(results)} relevant segments")

            # 格式化输出：包含内容 + 元信息（章节标题）
            formatted_results: List[str] = []
            for i, doc in enumerate(results, 1):
                # 提取章节标题
                headers = []
                if doc.metadata.get("Header 1"):
                    headers.append(doc.metadata["Header 1"])
                if doc.metadata.get("Header 2"):
                    headers.append(doc.metadata["Header 2"])
                if doc.metadata.get("Header 3"):
                    headers.append(doc.metadata["Header 3"])

                header_str = " > ".join(headers) if headers else "无章节信息"

                # 格式化
                formatted = f"""【结果 {i}】
章节: {header_str}

内容:
{doc.page_content}"""
                formatted_results.append(formatted)

            return "\n\n---\n\n".join(formatted_results)

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
