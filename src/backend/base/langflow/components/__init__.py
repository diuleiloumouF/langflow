"""LangFlow Components module."""

# LangFlow 组件模块
# 该模块将所有组件访问转发到 lfx.components，提供向后兼容性

from __future__ import annotations

from typing import Any

# 从 lfx.components 导入公开 API 列表
from lfx.components import __all__ as _lfx_all

__all__: list[str] = list(_lfx_all)


def __getattr__(attr_name: str) -> Any:
    """Forward attribute access to lfx.components."""
    # 将属性访问转发到 lfx.components
    from lfx import components

    return getattr(components, attr_name)


def __dir__() -> list[str]:
    """Forward dir() to lfx.components."""
    # 将 dir() 调用转发到 lfx.components
    return list(__all__)
