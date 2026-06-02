"""Compatibility layer for lfx.components.models.

This module redirects imports to lfx.components.models_and_agents for backward compatibility.
"""

# lfx.components.models 的兼容层。
# 该模块将导入重定向到 lfx.components.models_and_agents，以保持向后兼容性。

from __future__ import annotations

from typing import Any

# Import everything from models_and_agents to maintain backward compatibility
# 从 models_and_agents 导入所有内容，以保持向后兼容性
from lfx.components.models_and_agents import *  # noqa: F403
from lfx.components.models_and_agents import __all__  # noqa: F401


# Set up module-level __getattr__ to handle dynamic imports
# 设置模块级别的 __getattr__ 以处理动态导入
def __getattr__(attr_name: str) -> Any:
    """Redirect all attribute access to models_and_agents module."""
    # 将所有属性访问重定向到 models_and_agents 模块
    from lfx.components import models_and_agents

    if hasattr(models_and_agents, attr_name):
        return getattr(models_and_agents, attr_name)

    msg = f"module '{__name__}' has no attribute '{attr_name}'"
    raise AttributeError(msg)


def __dir__() -> list[str]:
    """Return the directory of available attributes."""
    # 返回可用属性的目录列表
    from lfx.components import models_and_agents

    return dir(models_and_agents)
