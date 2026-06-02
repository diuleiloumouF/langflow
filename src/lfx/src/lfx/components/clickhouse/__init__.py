# 启用延迟注解求值，避免循环导入问题
from __future__ import annotations

# 类型检查相关导入，运行时不执行
from typing import TYPE_CHECKING, Any

# 动态导入工具函数
from lfx.components._importing import import_mod

# 仅在类型检查时导入，避免运行时循环依赖
if TYPE_CHECKING:
    from .clickhouse import ClickhouseVectorStoreComponent

# 动态导入映射表：组件类名 -> 所在模块名
_dynamic_imports = {
    "ClickhouseVectorStoreComponent": "clickhouse",
}

# 模块公开导出的组件列表
__all__ = [
    "ClickhouseVectorStoreComponent",
]


# 通过属性访问实现延迟导入，仅在实际使用时才加载组件模块
def __getattr__(attr_name: str) -> Any:
    """Lazily import ClickHouse components on attribute access."""
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


# 限制 dir() 返回的属性列表，只包含公开导出的组件
def __dir__() -> list[str]:
    return list(__all__)
