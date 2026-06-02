# 向后兼容模块，用于 langflow.events.event_manager
# 旧版导入路径的重定向，实际实现在 lfx.events.event_manager 中
# Backwards compatibility module for langflow.events.event_manager
# This module redirects imports to the new lfx.events.event_manager module

# 从 lfx 包中导入事件管理相关的类和工厂函数
from lfx.events.event_manager import (
    EventCallback,  # 事件回调类型
    EventManager,  # 事件管理器类
    PartialEventCallback,  # 部分参数已绑定的事件回调类型
    create_default_event_manager,  # 创建默认事件管理器的工厂函数
    create_stream_tokens_event_manager,  # 创建流式 token 事件管理器的工厂函数
)

# 模块公开 API 列表，控制 from module import * 的行为
__all__ = [
    "EventCallback",
    "EventManager",
    "PartialEventCallback",
    "create_default_event_manager",
    "create_stream_tokens_event_manager",
]
