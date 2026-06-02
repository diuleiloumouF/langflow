# 从 lfx.inputs.constants 模块导入标签页选项相关的常量
from lfx.inputs.constants import MAX_TAB_OPTION_LENGTH, MAX_TAB_OPTIONS

# 定义该模块对外公开的接口，仅暴露两个标签页选项常量
__all__ = ["MAX_TAB_OPTIONS", "MAX_TAB_OPTION_LENGTH"]
