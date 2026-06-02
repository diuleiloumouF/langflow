# 导入 Composio 基类组件
from lfx.base.composio.composio_base import ComposioBaseComponent


# Bolna Composio API 组件，用于集成 Bolna 语音助手服务
class ComposioBolnaAPIComponent(ComposioBaseComponent):
    # 组件在界面上的显示名称
    display_name: str = "Bolna"
    # 组件图标标识
    icon = "Bolna"
    # 官方文档链接
    documentation: str = "https://docs.composio.dev"
    # Composio 应用名称，用于标识目标服务
    app_name = "bolna"

    def set_default_tools(self):
        """Set the default tools for Bolna component."""
        # 设置 Bolna 组件的默认工具集
