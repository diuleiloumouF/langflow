"""Agentics components for Langflow - LLM-powered data transformation and generation.

This module provides components that leverage the Agentics framework for:
- Semantic data transformation (aMap)
- Data aggregation and summarization (aReduce)
- Synthetic data generation (aGenerate)
"""

# Agentics 组件模块 - 提供基于 LLM 的数据转换和生成功能
# 包含三个核心组件：aMap（语义数据转换）、aReduce（数据聚合）、aGenerate（合成数据生成）

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    from .agenerate_component import AgenerateComponent
    from .amap_component import AMapComponent
    from .areduce_component import AreduceComponent

# 动态导入映射表：组件名称 -> 所在模块名称
# 用于延迟导入，避免在模块加载时立即导入所有组件
_dynamic_imports = {
    "AgenerateComponent": "agenerate_component",
    "AMapComponent": "amap_component",
    "AreduceComponent": "areduce_component",
}

# 导出的公共组件列表，供外部模块使用
__all__ = [
    "AMapComponent",
    "AgenerateComponent",
    "AreduceComponent",
]


# 延迟加载函数：在访问模块属性时动态导入组件
def __getattr__(attr_name: str) -> Any:
    """Lazily import agentics components on attribute access."""
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


# 自定义 dir() 函数，仅返回 __all__ 中定义的公共组件名称
def __dir__() -> list[str]:
    return list(__all__)
