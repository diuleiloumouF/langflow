# Groq 模型相关组件的初始化模块
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    from .groq import GroqModel

# 动态导入映射表，用于延迟加载组件
_dynamic_imports = {
    "GroqModel": "groq",
}

# 模块公开导出的组件列表
__all__ = [
    "GroqModel",
]


def __getattr__(attr_name: str) -> Any:
    """# 当访问模块属性时，延迟导入 Groq 相关的组件"""
    """Lazily import groq components on attribute access."""
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    """# 返回模块公开导出的所有组件名称"""
    return list(__all__)
