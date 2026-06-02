"""输入验证器模块。

从 lfx 包重新导出验证相关的类和函数，
供 langflow-base 平台层使用，避免直接依赖 lfx 内部路径。
"""

# 从 lfx 核心包导入验证器：CoalesceBool 用于布尔值的宽松校验，validate_boolean 用于布尔值格式验证
from lfx.inputs.validators import CoalesceBool, validate_boolean

# 控制模块的公开导出列表，仅暴露两个验证器符号
__all__ = ["CoalesceBool", "validate_boolean"]
