# 内容块模块 - 定义 Langflow 中用于表示不同类型内容块的 Pydantic 模型和类型
from typing import Annotated

from pydantic import BaseModel, Discriminator, Field, Tag, field_serializer, field_validator
from typing_extensions import TypedDict

from .content_types import CodeContent, ErrorContent, JSONContent, MediaContent, TextContent, ToolContent


def _get_type(d: dict | BaseModel) -> str | None:
    # 从字典或 Pydantic BaseModel 实例中提取 type 字段值，用于判别联合类型
    if isinstance(d, dict):
        return d.get("type")
    return getattr(d, "type", None)


# 创建所有内容类型的联合类型，使用 Pydantic 的判别联合模式进行类型区分
# Create a union type of all content types
ContentType = Annotated[
    Annotated[ToolContent, Tag("tool_use")]
    | Annotated[ErrorContent, Tag("error")]
    | Annotated[TextContent, Tag("text")]
    | Annotated[MediaContent, Tag("media")]
    | Annotated[CodeContent, Tag("code")]
    | Annotated[JSONContent, Tag("json")],
    Discriminator(_get_type),
]


# 内容块类 - 用于封装包含标题、多种内容类型列表及可选媒体 URL 的内容块
class ContentBlock(BaseModel):
    """A block of content that can contain different types of content."""

    # 内容块标题
    title: str
    # 内容列表，支持工具调用、错误、文本、媒体、代码和 JSON 等多种内容类型
    contents: list[ContentType]
    # 是否允许 Markdown 渲染，默认为 True
    allow_markdown: bool = Field(default=True)
    # 可选的媒体 URL 列表
    media_url: list[str] | None = None

    def __init__(self, **data) -> None:
        # 调用父类初始化后，遍历 Pydantic 核心 schema 中的字段，
        # 将有默认值的字段标记为已设置（已设置的字段不参与验证时的缺失报错）
        super().__init__(**data)
        schema_dict = self.__pydantic_core_schema__["schema"]
        if "fields" in schema_dict:
            fields = schema_dict["fields"]
        elif "schema" in schema_dict:
            fields = schema_dict["schema"]["fields"]
        fields_with_default = (f for f, d in fields.items() if "default" in d["schema"])
        self.model_fields_set.update(fields_with_default)

    @field_validator("contents", mode="before")
    @classmethod
    def validate_contents(cls, v) -> list[ContentType]:
        # 内容字段预校验：确保传入的是列表，单个 BaseModel 实例会被包装为列表
        if isinstance(v, dict):
            msg = "Contents must be a list of ContentTypes"
            raise TypeError(msg)
        return [v] if isinstance(v, BaseModel) else v

    @field_serializer("contents")
    def serialize_contents(self, value) -> list[dict]:
        # 序列化 contents 列表，将每个内容对象转换为字典
        return [v.model_dump() for v in value]


# ContentBlock 的 TypedDict 版本，用于类型提示和字典操作时的静态类型检查
class ContentBlockDict(TypedDict):
    title: str
    contents: list[dict]
    allow_markdown: bool
    media_url: list[str] | None
