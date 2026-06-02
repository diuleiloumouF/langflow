from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# TYPE_CHECKING 模块：仅在类型检查工具运行时导入，运行时不执行，避免循环导入
if TYPE_CHECKING:
    from .pgvector import PGVectorStoreComponent

# 动态导入映射表：键为组件名称，值为对应的子模块名称
# 通过延迟导入机制，在首次访问属性时才真正导入对应的组件模块
_dynamic_imports = {
    "PGVectorStoreComponent": "pgvector",
}

# 模块公开导出的组件列表，外部可通过 `from lfx.components.pgvector import PGVectorStoreComponent` 使用
__all__ = [
    "PGVectorStoreComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import pgvector components on attribute access."""
    # 当访问模块中不存在的属性时，触发延迟导入逻辑
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 调用 import_mod 工具函数，根据组件名和子模块名动态导入目标组件
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到模块全局字典中，后续访问不再重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 输出仅包含 __all__ 中声明的组件，隐藏内部实现细节
    return list(__all__)
