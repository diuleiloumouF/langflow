from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 仅在类型检查时导入，避免循环依赖和不必要的运行时开销
if TYPE_CHECKING:
    from .ollama import ChatOllamaComponent
    from .ollama_embeddings import OllamaEmbeddingsComponent

# 动态导入映射表：组件名 -> 所在模块名（不含包前缀）
_dynamic_imports = {
    "ChatOllamaComponent": "ollama",
    "OllamaEmbeddingsComponent": "ollama_embeddings",
}

# 模块公开导出的组件列表
__all__ = [
    "ChatOllamaComponent",
    "OllamaEmbeddingsComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import ollama components on attribute access.

    通过属性访问时懒加载导入 ollama 组件，避免在包初始化时加载所有组件。
    """
    # 如果请求的属性名不在动态导入映射中，直接报错
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 使用 import_mod 动态导入指定组件模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，后续访问不再重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 输出为 __all__ 中声明的组件，隐藏内部模块
    return list(__all__)
