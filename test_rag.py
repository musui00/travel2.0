"""单独测试 RAG 能力"""

from src.utils.rag_manager import RAGManager


def test_rag():
    """测试本地知识库检索"""
    print("=" * 50)
    print("测试 RAG 本地知识库检索")
    print("=" * 50)

    # 创建 RAG 管理器
    rag = RAGManager()

    # 加载 PDF 并创建向量库（首次运行）
    print("\n[1] 加载 PDF 并创建向量库...")
    try:
        rag.load_and_index()
        print("✅ 向量库创建成功")
    except FileNotFoundError as e:
        print(f"❌ PDF 文件不存在: {e}")
        return
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return

    # 测试查询
    test_questions = [
        "哈尔滨有哪些特色美食？",
        "中央大街附近有什么景点？",
        "去哈尔滨旅游的最佳时间是什么时候？",
    ]

    print("\n[2] 开始查询测试...")
    print("-" * 50)

    for question in test_questions:
        print(f"\n问题: {question}")
        print("-" * 30)
        result = rag.query(question)
        print(result[:500] if len(result) > 500 else result)
        print()


if __name__ == "__main__":
    test_rag()
