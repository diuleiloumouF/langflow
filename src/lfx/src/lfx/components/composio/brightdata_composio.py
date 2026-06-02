# 导入 Composio 基础组件类
from lfx.base.composio.composio_base import ComposioBaseComponent


# Brightdata API 组件，继承自 Composio 基础组件，用于集成 Brightdata 服务
class ComposioBrightdataAPIComponent(ComposioBaseComponent):
    # 组件在 UI 中显示的名称
    display_name: str = "Brightdata"
    # 组件图标名称
    icon = "Brightdata"
    # 组件文档链接
    documentation: str = "https://docs.composio.dev"
    # Composio 应用名称标识
    app_name = "brightdata"

    def set_default_tools(self):
        """Set the default tools for Brightdata component."""
        # 设置 Brightdata 组件的默认工具
