# 向后兼容模块：将导入重定向到新的 lfx.schema.graph 模块
from lfx.schema.graph import InputValue, Tweaks

__all__ = ["InputValue", "Tweaks"]
