from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 仅在类型检查时导入实际组件类，避免运行时不必要的加载开销
if TYPE_CHECKING:
    from lfx.components.anthropic.anthropic import AnthropicModelComponent

# 动态导入映射表：组件名 -> 子模块名，用于延迟加载
_dynamic_imports = {
    "AnthropicModelComponent": "anthropic",
}

# 模块公开导出的组件列表
__all__ = [
    "AnthropicModelComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import Anthropic components on attribute access."""
    # 属性访问时按需导入 Anthropic 组件，避免模块加载时的性能开销
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 使用动态导入工具从对应的子模块中加载组件类
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入的结果缓存到全局字典中，后续访问不再重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 仅暴露 __all__ 中声明的属性，保持模块接口整洁
    return list(__all__)
