from __future__ import annotations

# 允许在类型注解中使用前向引用（字符串形式的类型注解）
from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    from .faiss import FaissVectorStoreComponent

# 动态导入映射表：组件名称 -> 模块名称
_dynamic_imports = {
    "FaissVectorStoreComponent": "faiss",
}

# 模块的公开 API 列表
__all__ = [
    "FaissVectorStoreComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import FAISS components on attribute access."""
    # 属性访问时懒加载导入：仅在实际访问时才导入 FAISS 相关组件
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 根据动态导入映射表加载对应的模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入的结果缓存到全局命名空间中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 返回值为公开 API 列表，隐藏内部实现细节
    return list(__all__)
