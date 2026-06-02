# 日志和消息发送函数类型定义模块
# 定义了组件中使用的日志记录、消息发送和 token 流式处理的协议类型
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel
from typing_extensions import Protocol

from langflow.schema.message import ContentBlock, Message
from langflow.schema.playground_events import PlaygroundEvent

# 可记录的日志值类型别名
LoggableType: TypeAlias = str | dict | list | int | float | bool | BaseModel | PlaygroundEvent | None


# 日志函数协议：定义组件日志记录的接口
class LogFunctionType(Protocol):
    def __call__(self, message: LoggableType | list[LoggableType], *, name: str | None = None) -> None: ...


# 消息发送函数协议：定义向 Playground 发送消息的异步接口
class SendMessageFunctionType(Protocol):
    async def __call__(
        self,
        message: Message | None = None,
        text: str | None = None,
        background_color: str | None = None,
        text_color: str | None = None,
        icon: str | None = None,
        content_blocks: list[ContentBlock] | None = None,
        format_type: Literal["default", "error", "warning", "info"] = "default",
        id_: str | None = None,
        *,
        allow_markdown: bool = True,
    ) -> Message: ...


# Token 流式处理函数协议：定义处理流式 token 数据的接口
class OnTokenFunctionType(Protocol):
    def __call__(self, data: dict[str, Any]) -> None: ...
