from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    # 类型检查时仅导入 SupabaseVectorStoreComponent，避免运行时循环依赖
    from .supabase import SupabaseVectorStoreComponent

# 动态导入映射表：组件类名 -> 所属子模块名称
_dynamic_imports = {
    "SupabaseVectorStoreComponent": "supabase",
}

# 模块公开导出列表
__all__ = [
    "SupabaseVectorStoreComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import Supabase components on attribute access."""
    # 属性不在动态导入映射中，抛出 AttributeError
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过动态导入机制按需加载组件模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，后续访问不再重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    """返回模块的公开导出列表，供 dir() 函数使用。"""
    return list(__all__)
