from __future__ import annotations

from typing import TYPE_CHECKING, Any

# 从内部工具模块导入动态导入函数
from lfx.components._importing import import_mod

# 仅在类型检查时导入，避免运行时循环依赖
if TYPE_CHECKING:
    from .mistral import MistralAIModelComponent
    from .mistral_embeddings import MistralAIEmbeddingsComponent

# 动态导入映射表：组件名称 -> 所在模块名
_dynamic_imports = {
    "MistralAIModelComponent": "mistral",
    "MistralAIEmbeddingsComponent": "mistral_embeddings",
}

# 模块公开导出的组件列表
__all__ = [
    "MistralAIEmbeddingsComponent",
    "MistralAIModelComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import mistral components on attribute access."""
    # 当访问模块属性时，按需延迟导入对应的 mistral 组件
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 调用动态导入函数加载指定组件
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局字典中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 返回模块公开导出的组件名称列表
    return list(__all__)
