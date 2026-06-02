"""Component module for langflow - imports from lfx.

This maintains backward compatibility while using the lfx implementation.
"""

# langflow 组件模块 - 从 lfx 导入组件实现
# 该模块是一个兼容层，保持向后兼容性，同时使用 lfx 包中的实际实现

from lfx.custom.custom_component.component import (
    BACKWARDS_COMPATIBLE_ATTRIBUTES,
    CONFIG_ATTRIBUTES,
    Component,
    PlaceholderGraph,
    get_component_toolkit,
)

# 为了向后兼容 - 某些代码可能仍在使用这个私有函数名
_get_component_toolkit = get_component_toolkit

# 模块公开的 API 列表
__all__ = [
    "BACKWARDS_COMPATIBLE_ATTRIBUTES",
    "CONFIG_ATTRIBUTES",
    "Component",
    "PlaceholderGraph",
    "_get_component_toolkit",
    "get_component_toolkit",
]
