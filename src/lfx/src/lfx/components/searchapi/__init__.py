from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 类型检查时的条件导入
if TYPE_CHECKING:
    from lfx.components.searchapi.search import SearchComponent

# 动态导入映射：组件名 -> 模块名
_dynamic_imports = {
    "SearchComponent": "search",
}

# 定义模块公开的组件列表
__all__ = [
    "SearchComponent",
]


def __getattr__(attr_name: str) -> Any:
    # 当访问模块属性时，动态导入相应的searchapi组件
    """Lazily import searchapi components on attribute access."""
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 执行动态导入
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入的组件缓存到全局字典中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 返回模块中可用的组件列表
    return list(__all__)
