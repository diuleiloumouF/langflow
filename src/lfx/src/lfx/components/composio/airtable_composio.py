# 导入 Composio 基础组件类
from lfx.base.composio.composio_base import ComposioBaseComponent


# Composio Airtable API 组件，用于与 Airtable 进行集成操作
class ComposioAirtableAPIComponent(ComposioBaseComponent):
    # 在画布上显示的组件名称
    display_name: str = "Airtable"
    # 组件图标
    icon = "Airtable"
    # 官方文档链接
    documentation: str = "https://docs.composio.dev"
    # Composio 应用名称标识
    app_name = "airtable"

    # 设置 Airtable 组件的默认可用工具
    def set_default_tools(self):
        """Set the default tools for Airtable component."""
