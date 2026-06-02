"""Base component for Agentics components."""
# Agentics 组件的基础组件类

from __future__ import annotations

from typing import ClassVar

from lfx.base.models.unified_models import handle_model_input_update
from lfx.custom.custom_component.component import Component


class BaseAgenticComponent(Component):
    """Base class for Agentics components with shared configuration and model management.

    Provides common functionality for:
    - Dynamic model option updates based on user selection
    - Provider-specific field visibility management
    - Unified build configuration handling
    """

    # Agentics 组件的基类，提供共享配置和模型管理功能
    # 提供以下通用功能：
    # - 根据用户选择动态更新模型选项
    # - 管理特定于提供商的字段可见性
    # - 统一的构建配置处理

    display_name: str | bool = False  # Hide from sidebar - not meant to be used directly
    # 从侧边栏隐藏 - 此组件不打算直接使用

    code_class_base_inheritance: ClassVar[str | None] = None
    # 代码类的基础继承类名

    _code_class_base_inheritance: ClassVar[str | None] = None
    # 内部使用的代码类基础继承类名

    def update_build_config(
        self,
        build_config: dict,
        field_value: str,
        field_name: str | None = None,
    ) -> dict:
        """Dynamically update build configuration with user-filtered model options.

        Args:
            build_config: The current build configuration dictionary.
            field_value: The value of the field being updated.
            field_name: The name of the field being updated.

        Returns:
            Updated build configuration with filtered model options and adjusted field visibility.
        """
        # 动态更新构建配置，根据用户选择过滤模型选项
        # Args:
        #     build_config: 当前的构建配置字典。
        #     field_value: 正在更新的字段的值。
        #     field_name: 正在更新的字段名称。
        # Returns:
        #     更新后的构建配置，包含过滤后的模型选项和调整后的字段可见性。
        return handle_model_input_update(self, build_config, field_value, field_name)
