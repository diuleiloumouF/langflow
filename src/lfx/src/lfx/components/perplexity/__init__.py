from __future__ import annotations

from typing import TYPE_CHECKING, Any

# 从 lfx 组件导入工具模块，用于动态导入功能
from lfx.components._importing import import_mod

if TYPE_CHECKING:
    # 类型检查时才导入 PerplexityComponent，避免循环导入和运行时开销
    from .perplexity import PerplexityComponent

# 动态导入映射表：组件类名 -> 所在模块名
_dynamic_imports = {
    "PerplexityComponent": "perplexity",
}

# 模块公开导出的组件列表
__all__ = [
    "PerplexityComponent",
]


def __getattr__(attr_name: str) -> Any:
    """在属性访问时延迟导入 perplexity 组件。"""
    # 检查请求的属性是否在动态导入映射中
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 执行动态导入
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 返回模块公开导出的组件列表，控制 dir() 的输出
    return list(__all__)
