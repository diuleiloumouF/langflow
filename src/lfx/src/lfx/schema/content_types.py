from typing import Any, Literal

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field, model_serializer
from typing_extensions import TypedDict

from lfx.schema.encoders import CUSTOM_ENCODERS


class HeaderDict(TypedDict, total=False):
    """内容头部信息的类型定义，包含标题和图标"""

    title: str | None
    icon: str | None


class BaseContent(BaseModel):
    """Base class for all content types."""

    # 所有内容类型的基类，定义了公共字段和序列化逻辑

    type: str = Field(..., description="Type of the content")
    # 内容类型标识符
    duration: int | None = None
    # 可选的持续时间（毫秒）
    header: HeaderDict | None = Field(default_factory=dict)
    # 可选的头部信息

    def to_dict(self) -> dict[str, Any]:
        # 将模型实例转换为字典
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseContent":
        # 从字典数据创建模型实例
        return cls(**data)

    @model_serializer(mode="wrap")
    def serialize_model(self, nxt) -> dict[str, Any]:
        # 自定义模型序列化，使用自定义编码器处理特殊类型
        try:
            dump = nxt(self)
            return jsonable_encoder(dump, custom_encoder=CUSTOM_ENCODERS)
        except Exception:  # noqa: BLE001
            # 当自定义编码器失败时，回退到默认序列化
            return nxt(self)


class ErrorContent(BaseContent):
    """Content type for error messages."""

    # 错误消息内容类型，用于表示组件执行过程中的错误信息

    type: Literal["error"] = Field(default="error")
    # 内容类型固定为 "error"
    component: str | None = None
    # 出错的组件名称
    field: str | None = None
    # 出错的字段名称
    reason: str | None = None
    # 错误原因
    solution: str | None = None
    # 建议的解决方案
    traceback: str | None = None
    # 错误堆栈跟踪信息


class TextContent(BaseContent):
    """Content type for simple text content."""

    # 纯文本内容类型，用于表示简单的文本输出

    type: Literal["text"] = Field(default="text")
    # 内容类型固定为 "text"
    text: str
    # 文本内容
    duration: int | None = None
    # 可选的持续时间


class MediaContent(BaseContent):
    """Content type for media content."""

    # 媒体内容类型，用于表示图片、视频等媒体资源

    type: Literal["media"] = Field(default="media")
    # 内容类型固定为 "media"
    urls: list[str]
    # 媒体资源的 URL 列表
    caption: str | None = None
    # 可选的媒体说明文字


class JSONContent(BaseContent):
    """Content type for JSON content."""

    # JSON 内容类型，用于表示结构化的 JSON 数据

    type: Literal["json"] = Field(default="json")
    # 内容类型固定为 "json"
    data: dict[str, Any]
    # JSON 数据内容


class CodeContent(BaseContent):
    """Content type for code snippets."""

    # 代码片段内容类型，用于表示带语法高亮的代码

    type: Literal["code"] = Field(default="code")
    # 内容类型固定为 "code"
    code: str
    # 代码文本
    language: str
    # 编程语言标识（如 python、javascript 等）
    title: str | None = None
    # 可选的代码片段标题


class ToolContent(BaseContent):
    """Content type for tool start content."""

    # 工具调用内容类型，用于表示工具的调用输入、输出和错误信息

    model_config = ConfigDict(populate_by_name=True)
    # 允许通过字段名或别名来填充字段

    type: Literal["tool_use"] = Field(default="tool_use")
    # 内容类型固定为 "tool_use"
    name: str | None = None
    # 工具名称
    tool_input: dict[str, Any] = Field(default_factory=dict, alias="input")
    # 工具调用的输入参数（JSON 格式），别名为 "input"
    output: Any | None = None
    # 工具调用的输出结果
    error: Any | None = None
    # 工具调用的错误信息
    duration: int | None = None
    # 工具调用的持续时间
