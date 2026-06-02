from lfx.base.composio.composio_base import ComposioBaseComponent


class ComposioBitbucketAPIComponent(ComposioBaseComponent):
    """Composio Bitbucket API 组件，用于与 Bitbucket 服务进行集成"""

    # 显示名称，用于在界面上展示
    display_name: str = "Bitbucket"
    # 组件图标
    icon = "Bitbucket"
    # 文档链接
    documentation: str = "https://docs.composio.dev"
    # 应用名称标识
    app_name = "bitbucket"

    def set_default_tools(self):
        """Set the default tools for Bitbucket component."""
        # 设置 Bitbucket 组件的默认工具集
