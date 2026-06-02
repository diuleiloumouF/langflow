# Weaviate 向量存储组件包，提供 Weaviate 向量数据库的存储和搜索功能
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    from .weaviate import WeaviateVectorStoreComponent

# 动态导入映射表：组件名称 -> 模块名称，用于延迟加载
_dynamic_imports = {
    "WeaviateVectorStoreComponent": "weaviate",
}

__all__ = [
    "WeaviateVectorStoreComponent",
]


def __getattr__(attr_name: str) -> Any:
    """延迟导入 Weaviate 组件，在属性访问时才真正导入。

    Lazily import Weaviate components on attribute access.
    """
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
    """返回模块的公开导出列表"""
    return list(__all__)
