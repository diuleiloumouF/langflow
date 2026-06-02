# 转发导入：转换器工具函数
# 我们有意保留此文件，因为 components/__init__.py 中对 lfx 的重定向
# 仅支持从 lfx.components 的直接导入，不支持子模块。
#
# 这使得从 langflow.components.processing.converter 导入仍然可以正常工作。
from lfx.components.processing.converter import convert_to_dataframe

__all__ = ["convert_to_dataframe"]
