from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    # 类型检查时导入，避免循环导入
    from lfx.components.maritalk.maritalk import MaritalkModelComponent

# 动态导入映射表：组件类名 -> 模块名
_dynamic_imports = {
    "MaritalkModelComponent": "maritalk",
}

# 公开导出的组件列表
__all__ = ["MaritalkModelComponent"]


def __getattr__(attr_name: str) -> Any:
    """Lazily import maritalk components on attribute access.

    通过属性访问时懒加载导入 maritalk 组件。
    只有在实际访问组件属性时才会触发导入，避免不必要的模块加载。
    """
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 使用通用导入函数加载对应的组件模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到模块全局命名空间中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 控制 dir() 的返回值，仅暴露 __all__ 中定义的组件
    return list(__all__)
