# AIML 组件包初始化模块
# 提供 AIML 模型组件和嵌入组件的延迟加载功能

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 类型检查时导入，避免循环依赖
if TYPE_CHECKING:
    from lfx.components.aiml.aiml import AIMLModelComponent
    from lfx.components.aiml.aiml_embeddings import AIMLEmbeddingsComponent

# 动态导入映射表：组件名 -> 模块名
# 用于延迟加载组件，减少启动时的导入开销
_dynamic_imports = {
    "AIMLModelComponent": "aiml",
    "AIMLEmbeddingsComponent": "aiml_embeddings",
}

# 公开导出的组件列表
__all__ = [
    "AIMLEmbeddingsComponent",
    "AIMLModelComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import aiml components on attribute access."""
    # 检查组件名是否在动态导入映射表中
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 延迟导入组件，仅在首次访问时加载
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 缓存导入结果到全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    """返回模块中公开导出的组件列表，用于 dir() 函数。"""
    return list(__all__)
