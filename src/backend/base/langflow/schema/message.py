"""Message class for langflow - imports from lfx.

This maintains backward compatibility while using the lfx implementation.
"""

# 从 lfx 模块导入消息相关类型，保持类身份一致性
from lfx.schema.message import (
    MAX_ATTACHMENT_SIZE_BYTES,
    ContentBlock,
    DefaultModel,
    ErrorMessage,
    Message,
    MessageResponse,
)

__all__ = [
    "MAX_ATTACHMENT_SIZE_BYTES",
    "ContentBlock",
    "DefaultModel",
    "ErrorMessage",
    "Message",
    "MessageResponse",
]
