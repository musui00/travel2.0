from src.utils.rag_manager import RAGManager
import os

if __name__ == "__main__":
    print("🚀 正在初始化本地 RAG 向量库...")
    print(
        "⏳ 如果是首次运行，后台正在下载 m3e-base 模型，请耐心等待（可能需要几分钟）..."
    )

    rag = RAGManager(markdown_path="data_markdown/哈尔滨旅游攻略.md")
    rag.load_and_index()  # 触发 Markdown 解析、向量化和持久化

    if os.path.exists("./chroma_db_md"):
        print("✅ 恭喜！chroma_db_md 目录已成功创建，向量数据已落盘！")
    else:
        print("❌ 创建失败，请检查报错信息。")
