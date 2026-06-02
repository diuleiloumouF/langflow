# UUID 解析工具函数测试模块
# 测试 parse_uuid 函数对各种输入类型的处理（UUID、字符串、无效类型等）
from uuid import UUID

import pytest
from langflow.services.database.utils import parse_uuid


class TestParseUuid:
    """Tests for the shared parse_uuid utility."""

    # 共享 parse_uuid 工具函数的测试

    def test_passthrough_uuid(self):
        """测试 UUID 输入直接传递。"""
        uid = UUID("12345678-1234-5678-1234-567812345678")
        assert parse_uuid(uid) is uid

    def test_valid_string_uuid(self):
        """测试有效字符串 UUID 解析。"""
        raw = "12345678-1234-5678-1234-567812345678"
        result = parse_uuid(raw)
        assert isinstance(result, UUID)
        assert str(result) == raw

    def test_strips_whitespace(self):
        """测试去除首尾空白字符。"""
        raw = "  12345678-1234-5678-1234-567812345678  "
        result = parse_uuid(raw)
        assert str(result) == "12345678-1234-5678-1234-567812345678"

    def test_empty_string_raises(self):
        """测试空字符串抛出 ValueError。"""
        with pytest.raises(ValueError, match="must not be empty"):
            parse_uuid("")

    def test_whitespace_only_raises(self):
        """测试仅空白字符串抛出 ValueError。"""
        with pytest.raises(ValueError, match="must not be empty"):
            parse_uuid("   ")

    def test_invalid_string_raises_with_field_name(self):
        """测试无效字符串抛出 ValueError，包含字段名。"""
        with pytest.raises(ValueError, match="my_field is not a valid UUID"):
            parse_uuid("not-a-uuid", field_name="my_field")

    def test_default_field_name_in_error(self):
        """测试错误信息中使用默认字段名。"""
        with pytest.raises(ValueError, match="value is not a valid UUID"):
            parse_uuid("not-a-uuid")

    def test_unsupported_type_raises_type_error(self):
        """测试不支持的类型抛出 TypeError。"""
        with pytest.raises(TypeError, match="my_field must be a UUID or string, got int"):
            parse_uuid(12345, field_name="my_field")  # type: ignore[arg-type]

    def test_unsupported_type_default_field_name(self):
        """测试不支持的类型使用默认字段名。"""
        with pytest.raises(TypeError, match="value must be a UUID or string, got list"):
            parse_uuid([], field_name="value")  # type: ignore[arg-type]
