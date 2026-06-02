# 部署模型验证测试模块
# 测试 Deployment 模型的字段验证器和 DeploymentRead schema
from unittest.mock import MagicMock

import pytest
from langflow.services.database.models.deployment.model import Deployment, DeploymentRead


class TestDeploymentValidation:
    """Tests for Deployment model field validators."""

    # 测试 Deployment 模型字段验证器

    def _make_info(self, field_name: str) -> MagicMock:
        """创建模拟的 ValidationInfo 对象。"""
        info = MagicMock()
        info.field_name = field_name
        return info

    def test_rejects_empty_name(self):
        """测试拒绝空名称。"""
        with pytest.raises(ValueError, match="name must not be empty"):
            Deployment.validate_non_empty("", self._make_info("name"))

    def test_rejects_whitespace_name(self):
        """测试拒绝空白名称。"""
        with pytest.raises(ValueError, match="name must not be empty"):
            Deployment.validate_non_empty("   ", self._make_info("name"))

    def test_rejects_empty_resource_key(self):
        """测试拒绝空资源键。"""
        with pytest.raises(ValueError, match="resource_key must not be empty"):
            Deployment.validate_non_empty("", self._make_info("resource_key"))

    def test_rejects_whitespace_resource_key(self):
        """测试拒绝空白资源键。"""
        with pytest.raises(ValueError, match="resource_key must not be empty"):
            Deployment.validate_non_empty("   ", self._make_info("resource_key"))

    def test_strips_whitespace_from_name(self):
        """测试去除名称首尾空白字符。"""
        result = Deployment.validate_non_empty("  hello  ", self._make_info("name"))
        assert result == "hello"

    def test_strips_whitespace_from_resource_key(self):
        """测试去除资源键首尾空白字符。"""
        result = Deployment.validate_non_empty("  rk-1  ", self._make_info("resource_key"))
        assert result == "rk-1"


class TestDeploymentRead:
    """Tests for DeploymentRead schema."""

    # 测试 DeploymentRead schema

    def test_has_expected_fields(self):
        """测试具有预期的字段。"""
        expected = {
            "id",
            "resource_key",
            "user_id",
            "project_id",
            "deployment_provider_account_id",
            "name",
            "description",
            "deployment_type",
            "created_at",
            "updated_at",
        }
        assert set(DeploymentRead.model_fields.keys()) == expected
