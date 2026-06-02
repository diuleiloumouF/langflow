from lfx.base.composio.composio_base import ComposioBaseComponent


# Apollo API 组件，用于集成 Composio 平台的 Apollo 服务
class ComposioApolloAPIComponent(ComposioBaseComponent):
    # 在画布上显示的组件名称
    display_name: str = "Apollo"
    # 组件图标
    icon = "Apollo"
    # 组件文档链接
    documentation: str = "https://docs.composio.dev"
    # Composio 应用名称标识
    app_name = "apollo"

    def set_default_tools(self):
        """Set the default tools for Apollo component."""
        # 设置 Apollo 组件的默认工具集
