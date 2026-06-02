from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 仅在类型检查时导入，避免循环依赖和运行时开销
if TYPE_CHECKING:
    from lfx.components.openrouter.openrouter import OpenRouterComponent

# 动态导入映射表：组件类名 -> 子模块名称
_dynamic_imports = {
    "OpenRouterComponent": "openrouter",
}

# 模块公开导出列表，控制 from xxx import * 的行为
__all__ = ["OpenRouterComponent"]


def __getattr__(attr_name: str) -> Any:
    """Lazily import openrouter components on attribute access."""
    # 检查属性名是否在动态导入映射中
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过辅助函数动态导入组件模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制模块的 dir() 输出为公开导出的组件列表
    return list(__all__)
