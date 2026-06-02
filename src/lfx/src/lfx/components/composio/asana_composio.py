# 导入 Composio 基础组件类
from lfx.base.composio.composio_base import ComposioBaseComponent


# Asana Composio API 组件类，用于集成 Asana 项目管理服务
class ComposioAsanaAPIComponent(ComposioBaseComponent):
    # 在画布上显示的组件名称
    display_name: str = "Asana"
    # 组件图标标识
    icon = "Asana"
    # 官方文档链接
    documentation: str = "https://docs.composio.dev"
    # 应用名称标识，用于 Composio 服务注册
    app_name = "asana"

    # 设置 Asana 组件的默认工具集
    def set_default_tools(self):
        """Set the default tools for Asana component.
        为 Asana 组件设置默认工具。
        """
