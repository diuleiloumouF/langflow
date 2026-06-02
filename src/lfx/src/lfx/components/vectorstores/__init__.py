from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    from .local_db import LocalDBComponent

# 向量存储组件的动态导入映射表
_dynamic_imports = {
    "LocalDBComponent": "local_db",
}

__all__ = [
    "LocalDBComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import vectorstore components on attribute access."""
    # 在访问属性时延迟导入向量存储组件
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
    return list(__all__)
