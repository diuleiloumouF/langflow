# 非空字符串验证工具函数测试模块
# 测试 validate_non_empty_string 函数对空字符串、空白字符串和正常字符串的处理
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langflow.services.database.utils import validate_non_empty_string


class TestValidateNonEmptyString:
    """Tests for the validate_non_empty_string utility."""

    # validate_non_empty_string 工具函数的测试

    def _make_info(self, field_name: str) -> MagicMock:
        """创建模拟的 ValidationInfo 对象。"""
        info = MagicMock()
        info.field_name = field_name
        return info

    def test_returns_stripped_value(self):
        """测试返回去除首尾空白的值。"""
        assert validate_non_empty_string("  hello  ", self._make_info("name")) == "hello"

    def test_passthrough_clean_value(self):
        """测试干净值直接传递。"""
        assert validate_non_empty_string("hello", self._make_info("name")) == "hello"

    def test_empty_string_raises_with_field_name(self):
        """测试空字符串抛出 ValueError，包含字段名。"""
        with pytest.raises(ValueError, match="name must not be empty"):
            validate_non_empty_string("", self._make_info("name"))

    def test_whitespace_only_raises(self):
        """测试仅空白字符串抛出 ValueError。"""
        with pytest.raises(ValueError, match="provider_url must not be empty"):
            validate_non_empty_string("   ", self._make_info("provider_url"))

    def test_fallback_field_name_when_info_lacks_attribute(self):
        """When info has no field_name attribute, falls back to 'Field'."""
        # 当 info 没有 field_name 属性时，回退到 'Field'
        info = object()  # no field_name attribute（没有 field_name 属性）
        with pytest.raises(ValueError, match="Field must not be empty"):
            validate_non_empty_string("", info)
