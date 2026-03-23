"""RAG Manager for local knowledge base retrieval using Parent Document Retriever."""

import re
import uuid
from pathlib import Path
from typing import List, Sequence

from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import run_in_executor
from langchain_core.stores import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils.logger import logger


def clean_text(text: str) -> str:
    """清洗 PDF 提取的文本，去除乱码和特殊字符."""
    # 移除控制字符，保留中文、英文、数字、常用标点
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    # 替换多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 移除行首行尾空白
    text = text.strip()
    return text


class ParentDocumentRetriever(BaseRetriever):
    """Parent Document Retriever implementation.

    Retrieves parent documents based on child chunk similarity search.
    - Child chunks are stored in vectorstore for precise retrieval
    - Parent documents are stored in docstore for complete context
    """

    vectorstore: Chroma
    docstore: InMemoryStore
    child_splitter: RecursiveCharacterTextSplitter
    parent_splitter: RecursiveCharacterTextSplitter

    def _get_relevant_documents(self, query: str) -> Sequence[Document]:
        """Get relevant parent documents for the query.

        Args:
            query: The search query.

        Returns:
            List of relevant parent documents.
        """
        # Search child chunks in vectorstore
        child_results = self.vectorstore.similarity_search(query, k=4)

        # Get unique parent document IDs from child results
        parent_ids = set()
        parent_docs = []

        for child_doc in child_results:
            # Extract parent ID from child doc metadata
            parent_id = child_doc.metadata.get("parent_id")
            if parent_id and parent_id not in parent_ids:
                parent_ids.add(parent_id)
                # Fetch parent document from docstore
                parent_content = self.docstore.mget([parent_id])
                if parent_content and parent_content[0]:
                    parent_docs.append(
                        Document(
                            page_content=parent_content[0],
                            metadata=child_doc.metadata.copy(),
                        )
                    )

        if not parent_docs:
            # Fallback: return child results as-is if no parent found
            logger.warning("No parent documents found, returning child chunks")
            return child_results

        return parent_docs

    async def _aget_relevant_documents(self, query: str) -> Sequence[Document]:
        """Async version of document retrieval."""
        return await run_in_executor(None, self._get_relevant_documents, query)


class RAGManager:
    """Manages local PDF document loading, embedding, and retrieval.

    Uses Parent Document Retriever architecture:
    - Child chunks (small) for precise retrieval
    - Parent documents (large) for complete context
    """

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

        # Parent splitter: chunk_size=1200, chunk_overlap=0 for complete context
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=0,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"],
        )

        # Child splitter: chunk_size=250, chunk_overlap=50 for precise retrieval
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=250,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"],
        )

        # Vector store for child chunks (persisted)
        self.vectorstore: Chroma | None = None

        # Store for parent documents (in-memory)
        self.docstore: InMemoryStore | None = None

        # Parent Document Retriever
        self.retriever: ParentDocumentRetriever | None = None

    def _load_pdf(self) -> List[Document]:
        """Load PDF and clean text.

        Returns:
            List of loaded documents.
        """
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

            logger.info(f"Loaded {len(documents)} pages from PDF")
            return documents

        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            raise

    def _init_vectorstore(self) -> Chroma:
        """Initialize or load the Chroma vector store.

        Returns:
            Chroma vector store instance.
        """
        persist_path = Path(self.persist_directory)

        # Check if vector store already exists
        if persist_path.exists():
            try:
                logger.info(f"Loading existing vector store from: {self.persist_directory}")
                vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                )
                # Verify it's not empty
                if vectorstore._collection.count() > 0:
                    logger.info(f"Loaded existing vector store with {vectorstore._collection.count()} chunks")
                    return vectorstore
                else:
                    logger.info("Existing vector store is empty, recreating...")
            except Exception as e:
                logger.warning(f"Failed to load existing vector store: {e}, recreating...")

        # Create new vector store
        logger.info(f"Creating new vector store at: {self.persist_directory}")
        vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )
        return vectorstore

    def load_and_index(self) -> None:
        """Load PDF and create vector store with Parent Document Retriever."""
        try:
            # Step 1: Load PDF
            documents = self._load_pdf()

            # Step 2: Split into parent documents (larger chunks for context)
            logger.info("Splitting documents into parent chunks (size=1200)...")
            parent_docs = self.parent_splitter.split_documents(documents)
            logger.info(f"Created {len(parent_docs)} parent documents")

            # Step 3: Split parent docs into child chunks (smaller for precision)
            logger.info("Splitting parent docs into child chunks (size=250)...")
            child_docs = self.child_splitter.split_documents(parent_docs)
            logger.info(f"Created {len(child_docs)} child chunks")

            # Step 4: Initialize in-memory store for parent documents
            self.docstore = InMemoryStore()

            # Step 5: Store parent documents in docstore with IDs
            logger.info("Storing parent documents in docstore...")
            parent_ids = []
            for i, parent_doc in enumerate(parent_docs):
                parent_id = f"parent_{i}"
                parent_ids.append(parent_id)
                parent_doc.metadata["parent_id"] = parent_id
                self.docstore.mset([(parent_id, parent_doc.page_content)])

            # Step 6: Add parent_id to child docs metadata
            for child_doc in child_docs:
                # Find which parent this child belongs to
                for i, parent_doc in enumerate(parent_docs):
                    # Check if child is part of parent by content overlap
                    if child_doc.page_content in parent_doc.page_content:
                        child_doc.metadata["parent_id"] = f"parent_{i}"
                        break

            # Step 7: Initialize vector store for child chunks
            self.vectorstore = self._init_vectorstore()

            # Step 8: Clear and repopulate vector store
            logger.info("Adding child chunks to vector store...")
            self.vectorstore.delete_collection()
            self.vectorstore = Chroma.from_documents(
                documents=child_docs,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
            )

            # Step 9: Assemble ParentDocumentRetriever
            logger.info("Assembling ParentDocumentRetriever...")
            self.retriever = ParentDocumentRetriever(
                vectorstore=self.vectorstore,
                docstore=self.docstore,
                child_splitter=self.child_splitter,
                parent_splitter=self.parent_splitter,
            )

            logger.info("Parent Document Retriever initialized and persisted successfully")

        except Exception as e:
            logger.error(f"Failed to load and index PDF: {e}")
            raise

    def load_existing(self) -> None:
        """Load existing vector store and reconstruct retriever."""
        persist_path = Path(self.persist_directory)

        if not persist_path.exists():
            logger.error(f"Vector store not found at: {self.persist_directory}")
            raise FileNotFoundError(
                f"Vector store not found at: {self.persist_directory}. "
                "Please run load_and_index() first."
            )

        try:
            # Load existing vector store
            logger.info(f"Loading existing vector store from: {self.persist_directory}")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )

            count = self.vectorstore._collection.count()
            logger.info(f"Loaded vector store with {count} child chunks")

            # Initialize in-memory store for parent documents
            # Need to re-split parent documents
            self.docstore = InMemoryStore()

            # Re-split and store parent documents
            logger.info("Re-splitting parent documents for docstore...")
            documents = self._load_pdf()
            parent_docs = self.parent_splitter.split_documents(documents)

            # Store parent documents in docstore with IDs
            for i, parent_doc in enumerate(parent_docs):
                parent_id = f"parent_{i}"
                parent_doc.metadata["parent_id"] = parent_id
                self.docstore.mset([(parent_id, parent_doc.page_content)])

            # Reconstruct the retriever
            logger.info("Reconstructing ParentDocumentRetriever...")
            self.retriever = ParentDocumentRetriever(
                vectorstore=self.vectorstore,
                docstore=self.docstore,
                child_splitter=self.child_splitter,
                parent_splitter=self.parent_splitter,
            )

            logger.info("Existing retriever loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load existing retriever: {e}")
            raise

    def query(self, question: str, k: int = 3) -> str:
        """Query the retriever for relevant text segments.

        Args:
            question: The query string.
            k: Number of documents to retrieve (unused, kept for compatibility).

        Returns:
            Concatenated string of the relevant text segments.
        """
        if self.retriever is None:
            # Try to load existing, if not found, create new
            try:
                self.load_existing()
            except FileNotFoundError:
                logger.info("No existing retriever found, creating new one...")
                self.load_and_index()

        try:
            logger.info(f"Querying: {question}")

            # Use the retriever to get relevant documents
            results = self.retriever.invoke(question)

            if not results:
                logger.warning("No relevant documents found")
                return "未找到相关内容"

            # Extract content from results
            relevant_texts = [doc.page_content for doc in results]
            logger.info(f"Found {len(relevant_texts)} relevant segments")

            return "\n\n---\n\n".join(relevant_texts)

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
