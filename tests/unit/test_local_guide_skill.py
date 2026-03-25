"""
本地知识库检索 Skill 单元测试
使用 mock 避免真实加载模型和 PDF
"""

import pytest
from unittest.mock import patch, MagicMock

from src.skills.local_guide_skill import search_local_guide


class TestLocalGuideSkill:
    """测试本地知识库检索工具"""

    @patch("src.skills.local_guide_skill._get_rag_manager")
    def test_search_local_guide_success(self, mock_get_rag_manager):
        """测试正常查询场景"""
        # Mock RAGManager 实例
        mock_rag = MagicMock()
        mock_rag.query.return_value = (
            "中央大街是哈尔滨最繁华的商业街，全长1450米。\n\n"
            "---\n\n"
            "防洪纪念塔位于中央大街北端，是哈尔滨的标志性建筑。\n\n"
            "---\n\n"
            "索菲亚教堂是远东地区最大的东正教教堂，建筑风格独特。"
        )
        mock_get_rag_manager.return_value = mock_rag

        # 调用工具
        result = search_local_guide.invoke({"query": "哈尔滨中央大街有什么景点"})

        # 验证结果
        assert "中央大街" in result
        assert "防洪纪念塔" in result
        assert "索菲亚教堂" in result
        mock_rag.query.assert_called_once_with("哈尔滨中央大街有什么景点")

    @patch("src.skills.local_guide_skill._get_rag_manager")
    def test_search_local_guide_empty_query(self, mock_get_rag_manager):
        """测试空查询"""
        result = search_local_guide.invoke({"query": ""})

        assert "请提供有效的查询内容" in result
        mock_get_rag_manager.assert_not_called()

    @patch("src.skills.local_guide_skill._get_rag_manager")
    def test_search_local_guide_file_not_found(self, mock_get_rag_manager):
        """测试文件不存在场景"""
        from pathlib import Path

        mock_get_rag_manager.side_effect = FileNotFoundError(
            "PDF file not found: data/我是驴友-哈尔滨旅游攻略.pdf"
        )

        result = search_local_guide.invoke({"query": "哈尔滨美食"})

        assert "暂时不可用" in result or "不存在" in result

    @patch("src.skills.local_guide_skill._get_rag_manager")
    def test_search_local_guide_general_exception(self, mock_get_rag_manager):
        """测试通用异常场景"""
        mock_rag = MagicMock()
        mock_rag.query.side_effect = RuntimeError("Vector store error")
        mock_get_rag_manager.return_value = mock_rag

        result = search_local_guide.invoke({"query": "测试"})

        assert "错误" in result or "抱歉" in result

    def test_search_local_guide_direct_call(self):
        """测试直接调用工具函数（通过 invoke）"""
        with patch("src.skills.local_guide_skill._get_rag_manager") as mock_get_rag:
            mock_rag = MagicMock()
            mock_rag.query.return_value = "测试返回结果"
            mock_get_rag.return_value = mock_rag

            # 使用 invoke 调用
            result = search_local_guide.invoke({"query": "测试查询"})

            assert result == "测试返回结果"
            mock_rag.query.assert_called_once_with("测试查询")


class TestLocalGuideInput:
    """测试 Pydantic 输入验证"""

    def test_valid_query(self):
        """测试有效查询"""
        from src.skills.local_guide_skill import LocalGuideInput

        input_obj = LocalGuideInput(query="哈尔滨美食推荐")
        assert input_obj.query == "哈尔滨美食推荐"

    def test_empty_query_validation(self):
        """测试空查询验证（Pydantic 默认会处理）"""
        from src.skills.local_guide_skill import LocalGuideInput

        # 空字符串可以通过验证，只是业务逻辑层会处理
        input_obj = LocalGuideInput(query="")
        assert input_obj.query == ""
