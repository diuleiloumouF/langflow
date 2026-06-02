# custom_component 包初始化模块
# 该模块从底层 lfx 包中重新导出自定义组件相关的模块和类

from lfx.custom.custom_component import component, custom_component
from lfx.custom.custom_component.component import Component

# 定义模块的公共 API，明确导出的符号
__all__ = ["Component", "component", "custom_component"]
