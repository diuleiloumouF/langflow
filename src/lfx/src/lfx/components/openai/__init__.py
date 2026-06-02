# OpenAI 组件包的初始化模块，提供延迟加载机制
from __future__ import annotations

from typing import TYPE_CHECKING, Any

# 导入动态模块加载工具函数
from lfx.components._importing import import_mod

# 类型检查时的导入，避免循环依赖和运行时开销
if TYPE_CHECKING:
    from lfx.components.openai.openai import OpenAIEmbeddingsComponent
    from lfx.components.openai.openai_chat_model import OpenAIModelComponent

# 动态导入映射表：组件名称 -> 模块文件名（不带 .py 后缀）
_dynamic_imports = {
    "OpenAIEmbeddingsComponent": "openai",
    "OpenAIModelComponent": "openai_chat_model",
}

# 模块的公开 API 列表
__all__ = [
    "OpenAIEmbeddingsComponent",
    "OpenAIModelComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import OpenAI components on attribute access."""
    # 当访问模块属性时，延迟导入对应的组件类
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过动态导入工具加载指定组件
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入的结果缓存到模块全局字典中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 自定义 dir() 的返回值，仅展示公开 API 中定义的组件
    return list(__all__)
