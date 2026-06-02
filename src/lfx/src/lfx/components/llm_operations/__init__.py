# LLM 操作组件包
# 提供批量运行、智能转换、条件路由、LLM选择器和结构化输出等组件的懒加载导入

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# TYPE_CHECKING 块：仅在类型检查时导入，避免运行时开销
if TYPE_CHECKING:
    from lfx.components.llm_operations.batch_run import BatchRunComponent
    from lfx.components.llm_operations.lambda_filter import SmartTransformComponent
    from lfx.components.llm_operations.llm_conditional_router import SmartRouterComponent
    from lfx.components.llm_operations.llm_selector import LLMSelectorComponent
    from lfx.components.llm_operations.structured_output import StructuredOutputComponent

# 动态导入映射表：组件名称 -> 所在模块名
# 用于 __getattr__ 实现懒加载，只有在实际访问时才导入对应模块
_dynamic_imports = {
    "BatchRunComponent": "batch_run",
    "SmartTransformComponent": "lambda_filter",
    "SmartRouterComponent": "llm_conditional_router",
    "LLMSelectorComponent": "llm_selector",
    "StructuredOutputComponent": "structured_output",
}

# 公开导出的组件列表，供 IDE 自动补全和 from package import * 使用
__all__ = [
    "BatchRunComponent",
    "LLMSelectorComponent",
    "SmartRouterComponent",
    "SmartTransformComponent",
    "StructuredOutputComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import LLM operation components on attribute access."""
    # 当访问模块中不存在的属性时，尝试从动态导入表中懒加载对应组件
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 自定义 dir() 输出，仅暴露 __all__ 中声明的组件名称
    return list(__all__)
