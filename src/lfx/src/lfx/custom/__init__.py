# 自定义组件包，提供自定义组件基类和相关工具
from lfx.custom.custom_component.component import Component  # 组件基类，用于构建自定义组件
from lfx.custom.custom_component.custom_component import CustomComponent  # 自定义组件类，继承自 Component

from . import custom_component as custom_component  # 自定义组件子模块
from . import utils as utils  # 工具函数模块

__all__ = ["Component", "CustomComponent", "custom_component", "utils"]
