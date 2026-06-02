from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    from .cuga_agent import CugaComponent

# 动态导入映射表：组件名称 -> 模块文件名（不含扩展名）
_dynamic_imports = {
    "CugaComponent": "cuga_agent",
}

# 模块公开导出的组件列表
__all__ = [
    "CugaComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import cuga components on attribute access."""
    # 访问属性时进行懒加载导入，避免模块启动时加载所有组件
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过统一的 import_mod 工具函数动态导入组件模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到模块全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 输出仅为公开导出的组件名称
    return list(__all__)
