from __future__ import annotations

# 启用延迟注解求值，避免循环导入问题
from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 仅在类型检查时导入实际组件类，避免运行时不必要的导入
if TYPE_CHECKING:
    from lfx.components.cometapi.cometapi import CometAPIComponent

# 动态导入映射表：组件类名 -> 子模块名
_dynamic_imports = {
    "CometAPIComponent": "cometapi",
}

# 模块公开导出的组件列表
__all__ = ["CometAPIComponent"]


def __getattr__(attr_name: str) -> Any:
    """Lazily import cometapi components on attribute access."""
    # 当访问模块属性时，延迟导入对应的组件，而非在模块加载时一次性全部导入
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过统一的 import_mod 工具函数加载指定组件子模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，后续访问不再重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 只显示 __all__ 中声明的组件，隐藏内部实现细节
    return list(__all__)
