# 自定义组件模块 - 提供懒加载机制以延迟导入 CustomComponent
from __future__ import annotations

from typing import TYPE_CHECKING, Any

# 导入动态模块加载工具
from lfx.components._importing import import_mod

# 仅在类型检查时导入，避免循环依赖和不必要的运行时开销
if TYPE_CHECKING:
    from .custom_component import CustomComponent

# 动态导入映射表：键为类名，值为对应的模块文件名（不含扩展名）
_dynamic_imports = {
    "CustomComponent": "custom_component",
}

# 模块的公开 API 列表
__all__ = [
    "CustomComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import custom components on attribute access."""
    # 检查请求的属性是否在动态导入映射中
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 执行动态导入，将模块中的类加载到内存
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，后续访问不再重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 返回模块的公开 API 列表，用于 dir() 函数和自动补全
    return list(__all__)
