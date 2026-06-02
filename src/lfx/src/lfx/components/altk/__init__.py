# 启用延迟注解以支持类型注解中的前向引用
from __future__ import annotations

from typing import TYPE_CHECKING, Any

# 导入动态模块加载工具函数
from lfx.components._importing import import_mod

# 类型检查时的导入，避免循环依赖
if TYPE_CHECKING:
    from .altk_agent import ALTKAgentComponent

# 动态导入映射表：键为组件类名，值为对应的模块文件名
_dynamic_imports = {
    "ALTKAgentComponent": "altk_agent",
}

# 模块的公开 API 列表
__all__ = [
    "ALTKAgentComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import altk components on attribute access."""
    # 延迟加载：仅在访问属性时才导入对应的组件模块
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 动态导入组件模块并返回组件类
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 返回模块的公开属性列表，支持自动补全
    return list(__all__)
