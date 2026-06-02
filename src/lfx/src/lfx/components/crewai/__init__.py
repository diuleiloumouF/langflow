from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 仅在类型检查时导入，避免运行时循环依赖
if TYPE_CHECKING:
    from .crewai import CrewAIAgentComponent
    from .hierarchical_crew import HierarchicalCrewComponent
    from .hierarchical_task import HierarchicalTaskComponent
    from .sequential_crew import SequentialCrewComponent
    from .sequential_task import SequentialTaskComponent
    from .sequential_task_agent import SequentialTaskAgentComponent

# 动态导入映射表：组件类名 -> 所在模块名
_dynamic_imports = {
    "CrewAIAgentComponent": "crewai",
    "HierarchicalCrewComponent": "hierarchical_crew",
    "HierarchicalTaskComponent": "hierarchical_task",
    "SequentialCrewComponent": "sequential_crew",
    "SequentialTaskAgentComponent": "sequential_task_agent",
    "SequentialTaskComponent": "sequential_task",
}

# 模块公开导出的组件列表
__all__ = [
    "CrewAIAgentComponent",
    "HierarchicalCrewComponent",
    "HierarchicalTaskComponent",
    "SequentialCrewComponent",
    "SequentialTaskAgentComponent",
    "SequentialTaskComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import crewai components on attribute access."""
    # 如果属性名不在动态导入映射中，抛出 AttributeError
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过 import_mod 动态加载对应的组件模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入的结果缓存到模块全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 只返回 __all__ 中声明的公开组件，隐藏内部导入机制
    return list(__all__)
