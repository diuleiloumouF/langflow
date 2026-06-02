# 导入 Composio 基础组件类
from lfx.base.composio.composio_base import ComposioBaseComponent


# Calendly API 组件 - 通过 Composio 集成提供日历调度功能
class ComposioCalendlyAPIComponent(ComposioBaseComponent):
    # 组件在界面上显示的名称
    display_name: str = "Calendly"
    # 组件图标
    icon = "Calendly"
    # Composio 官方文档链接
    documentation: str = "https://docs.composio.dev"
    # 对应的 Composio 应用名称
    app_name = "calendly"

    # 设置 Calendly 组件的默认工具集
    def set_default_tools(self):
        """Set the default tools for Calendly component."""
