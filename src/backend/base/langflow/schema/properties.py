# 消息属性模块
# 定义了消息的来源信息、Token 使用量和显示属性等数据模型
from typing import Literal

from pydantic import BaseModel, Field, field_serializer, field_validator


# 消息来源信息模型：记录消息的来源组件和显示名称
class Source(BaseModel):
    id: str | None = Field(default=None, description="The id of the source component.")
    display_name: str | None = Field(default=None, description="The display name of the source component.")
    source: str | None = Field(
        default=None,
        description="The source of the message. Normally used to display the model name (e.g. 'gpt-4o')",
    )


# LLM 响应的 Token 使用量信息
class Usage(BaseModel):
    """Token usage information from LLM responses."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


# 消息显示属性模型：控制消息在 Playground 中的显示方式
class Properties(BaseModel):
    text_color: str | None = None
    background_color: str | None = None
    edited: bool = False
    source: Source = Field(default_factory=Source)
    icon: str | None = None
    allow_markdown: bool = False
    positive_feedback: bool | None = None
    state: Literal["partial", "complete"] = "complete"
    targets: list = []
    usage: Usage | None = None
    build_duration: float | None = None

    @field_validator("source", mode="before")
    @classmethod
    def validate_source(cls, v):
        if isinstance(v, str):
            return Source(id=v, display_name=v, source=v)
        if v is None:
            return Source()
        return v

    @field_serializer("source")
    def serialize_source(self, value):
        if isinstance(value, Source):
            return value.model_dump()
        return value
