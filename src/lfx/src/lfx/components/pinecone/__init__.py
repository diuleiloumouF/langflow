from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    from .pinecone import PineconeVectorStoreComponent

# Pinecone 组件的动态导入映射表，key 为组件类名，value 为对应的模块名
_dynamic_imports = {
    "PineconeVectorStoreComponent": "pinecone",
}

# 定义模块的公开 API，只导出 PineconeVectorStoreComponent
__all__ = [
    "PineconeVectorStoreComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import Pinecone components on attribute access."""
    # 当访问模块属性时，根据动态导入映射表懒加载对应的组件
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 执行实际的模块导入操作
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        # 导入失败时，将原始错误包装为 AttributeError 并抛出
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到模块全局命名空间中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 自定义 dir() 返回值，只暴露 __all__ 中定义的公开组件
    return list(__all__)
