from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 仅在类型检查时导入 MilvusVectorStoreComponent，避免运行时循环依赖
if TYPE_CHECKING:
    from .milvus import MilvusVectorStoreComponent

# 动态导入映射表：组件名称 -> 模块名称，用于延迟加载
_dynamic_imports = {
    "MilvusVectorStoreComponent": "milvus",
}

# 模块公开导出的组件列表
__all__ = [
    "MilvusVectorStoreComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import Milvus components on attribute access."""
    # 当访问的属性不在动态导入映射中时，抛出 AttributeError
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    # 通过 import_mod 函数延迟导入组件模块
    try:
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入的结果缓存到全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 只返回 __all__ 中声明的组件，保持模块命名空间整洁
    return list(__all__)
