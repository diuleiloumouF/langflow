# Couchbase 向量存储组件模块
# 提供 Couchbase 向量存储的懒加载导入机制

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    from .couchbase import CouchbaseVectorStoreComponent

# 动态导入映射表：组件类名 -> 所属子模块名
_dynamic_imports = {
    "CouchbaseVectorStoreComponent": "couchbase",
}

# 模块公开导出的组件列表
__all__ = [
    "CouchbaseVectorStoreComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import Couchbase components on attribute access."""
    # 检查请求的属性是否在动态导入映射中
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过 import_mod 执行懒加载导入
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到模块全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 输出为模块公开导出的组件
    return list(__all__)
