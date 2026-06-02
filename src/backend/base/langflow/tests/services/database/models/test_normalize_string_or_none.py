# 字符串标准化工具函数测试模块
# 测试 normalize_string_or_none 函数对 None、空字符串和空白字符串的处理
from langflow.services.database.utils import normalize_string_or_none


class TestNormalizeStringOrNone:
    """字符串标准化函数测试类。"""

    def test_none_returns_none(self):
        """测试 None 输入返回 None。"""
        assert normalize_string_or_none(None) is None

    def test_empty_returns_none(self):
        """测试空字符串输入返回 None。"""
        assert normalize_string_or_none("") is None

    def test_whitespace_returns_none(self):
        """测试空白字符串输入返回 None。"""
        assert normalize_string_or_none("   ") is None

    def test_strips_and_returns(self):
        """测试去除首尾空白字符并返回。"""
        assert normalize_string_or_none("  hello  ") == "hello"

    def test_non_blank_passthrough(self):
        """测试非空白字符串直接返回。"""
        assert normalize_string_or_none("hello") == "hello"
