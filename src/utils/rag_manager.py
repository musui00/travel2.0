"""RAG Manager for local knowledge base retrieval."""

import re
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils.logger import logger


def clean_text(text: str) -> str:
    """清洗 PDF 提取的文本，去除乱码和特殊字符"""
    # 替换常见的 PDF 乱码字符
    replacements = {
        "\u0000": "",
        "\ufffd": "",
        "\\s+": " ",  # 多个空格合并
    }

    # 移除控制字符，保留中文、英文、数字、常用标点
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

    # 替换多余的空白字符
    text = re.sub(r'\s+', ' ', text)

    # 移除行首行尾空白
    text = text.strip()

    return text


class RAGManager:
    """Manages local PDF document loading, embedding, and retrieval."""

    def __init__(
        self,
        pdf_path: str = "data/我是驴友-哈尔滨旅游攻略.pdf",
        persist_directory: str = "./chroma_db",
        embedding_model: str = "moka-ai/m3e-base",
    ) -> None:
        """Initialize the RAG Manager.

        Args:
            pdf_path: Path to the PDF document.
            persist_directory: Directory to persist the vector database.
            embedding_model: HuggingFace embedding model name.
        """
        self.pdf_path = pdf_path
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": "cpu"},
        )
        self.vectorstore: Chroma | None = None

    def load_and_index(self) -> None:
        """Load PDF and create vector store with embeddings."""
        pdf_file = Path(self.pdf_path)

        if not pdf_file.exists():
            logger.error(f"PDF file not found: {self.pdf_path}")
            raise FileNotFoundError(
                f"PDF file not found: {self.pdf_path}. "
                "Please place the PDF file in the data directory."
            )

        try:
            logger.info(f"Loading PDF from: {self.pdf_path}")
            loader = PDFPlumberLoader(str(pdf_file))
            documents = loader.load()

            # 清洗文本，去除乱码
            for doc in documents:
                doc.page_content = clean_text(doc.page_content)

            logger.info(f"Loaded {len(documents)} pages, splitting text...")

            # 优化切分参数：增大 chunk_size，减少段落被切断
            # 增加 overlap 保证上下文连贯
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,      # 增大到 1000 字符
                chunk_overlap=150,    # 重叠 150 字符，保留上下文
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"],  # 优先按段落切分
            )
            splits = text_splitter.split_documents(documents)

            logger.info(f"Created {len(splits)} text chunks")

            logger.info(f"Creating vector store at: {self.persist_directory}")
            self.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
            )

            logger.info("Vector store created and persisted successfully")

        except Exception as e:
            logger.error(f"Failed to load and index PDF: {e}")
            raise

    def load_existing(self) -> None:
        """Load an existing vector store from disk."""
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
            logger.info("Vector store loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load existing vector store: {e}")
            raise

    def query(self, question: str) -> str:
        """Query the vector store for relevant text segments.

        Args:
            question: The query string.

        Returns:
            Concatenated string of the 3 most relevant text segments.
        """
        if self.vectorstore is None:
            try:
                self.load_existing()
            except FileNotFoundError:
                logger.info("No existing vector store found, creating new one...")
                self.load_and_index()

        try:
            logger.info(f"Querying: {question}")
            results = self.vectorstore.similarity_search(
                query=question,
                k=3,
            )

            relevant_texts = [doc.page_content for doc in results]
            logger.info(f"Found {len(relevant_texts)} relevant segments")

            return "\n\n---\n\n".join(relevant_texts)

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
