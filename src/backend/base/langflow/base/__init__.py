"""Backwards compatibility module for langflow.base.

This module imports from lfx.base to maintain compatibility with existing code
that expects to import from langflow.base.
"""

# 向后兼容模块：从 lfx.base 导入所有内容，以保持与现有代码的兼容性
# Import all base modules from lfx for backwards compatibility
from lfx.base import *  # noqa: F403
