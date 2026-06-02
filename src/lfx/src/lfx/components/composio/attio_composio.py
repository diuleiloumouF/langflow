# 导入 Composio 基础组件类
from lfx.base.composio.composio_base import ComposioBaseComponent


# Attio Composio API 组件类，用于集成 Attio CRM 平台的工具和功能
class ComposioAttioAPIComponent(ComposioBaseComponent):
    # 组件在界面上的显示名称
    display_name: str = "Attio"
    # 组件图标标识
    icon = "Attio"
    # Composio 官方文档链接
    documentation: str = "https://docs.composio.dev"
    # 应用名称，用于 Composio 服务端识别对应的集成服务
    app_name = "attio"

    def set_default_tools(self):
        """Set the default tools for Attio component."""
        # 设置 Attio 组件的默认工具集
