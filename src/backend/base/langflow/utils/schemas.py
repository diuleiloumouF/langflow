# API 响应 Schema 定义模块
# 定义了聊天输出、数据输出等 API 响应的数据模型
import enum
from typing import Any
from uuid import UUID

from langchain_core.messages import BaseMessage
from lfx.base.data.utils import IMG_FILE_TYPES, TEXT_FILE_TYPES
from lfx.utils.constants import MESSAGE_SENDER_AI, MESSAGE_SENDER_NAME_AI
from pydantic import BaseModel, field_validator, model_validator
from typing_extensions import TypedDict


# 文件信息字典类型，包含路径、名称和类型
class File(TypedDict):
    """File schema."""

    path: str
    name: str
    type: str


# 聊天输出响应模型：定义聊天 API 返回的数据结构
class ChatOutputResponse(BaseModel):
    """Chat output response schema."""

    message: str | list[str | dict]
    sender: str | None = MESSAGE_SENDER_AI
    sender_name: str | None = MESSAGE_SENDER_NAME_AI
    session_id: str | None = None
    """If set, must be a string. If a UUID type is provided,
    it will be converted to a string. No other types are accepted."""
    stream_url: str | None = None
    component_id: str | None = None
    files: list[File] = []
    type: str

    @field_validator("files", mode="before")
    @classmethod
    def validate_files(cls, files):
        """Validate files."""
        if not files:
            return files

        for file in files:
            if not isinstance(file, dict):
                msg = "Files must be a list of dictionaries."
                raise ValueError(msg)  # noqa: TRY004

            if not all(key in file for key in ["path", "name", "type"]):
                # If any of the keys are missing, we should extract the
                # values from the file path
                path = file.get("path")
                if not path:
                    msg = "File path is required."
                    raise ValueError(msg)

                name = file.get("name")
                if not name:
                    name = path.split("/")[-1]
                    file["name"] = name
                type_ = file.get("type")
                if not type_:
                    # get the file type from the path
                    extension = path.split(".")[-1]
                    file_types = set(TEXT_FILE_TYPES + IMG_FILE_TYPES)
                    if extension and extension in file_types:
                        type_ = extension
                    else:
                        for file_type in file_types:
                            if file_type in path:
                                type_ = file_type
                                break
                    if not type_:
                        msg = "File type is required."
                        raise ValueError(msg)
                file["type"] = type_

        return files

    @classmethod
    def from_message(
        cls,
        message: BaseMessage,
        sender: str | None = MESSAGE_SENDER_AI,
        sender_name: str | None = MESSAGE_SENDER_NAME_AI,
    ):
        """Build chat output response from message."""
        content = message.content
        return cls(message=content, sender=sender, sender_name=sender_name)

    @model_validator(mode="after")
    def validate_message(self):
        """Validate message."""
        # The idea here is ensure the \n in message
        # is compliant with markdown if sender is machine
        # so, for example:
        # \n\n -> \n\n
        # \n -> \n\n

        if self.sender != MESSAGE_SENDER_AI:
            return self

        # We need to make sure we don't duplicate \n
        # in the message
        message = self.message.replace("\n\n", "\n")
        self.message = message.replace("\n", "\n\n")
        return self

    @field_validator("session_id", mode="before")
    @classmethod
    def validate_and_coerce_session_id(cls, value: Any) -> str | None:
        """Validate and coerce session id to a string if it is a UUID.

        Must be a UUID, string, or None.
        If the session id is a UUID, it will be converted to a string.
        If the session id is a string or None, it will be returned as is.
        Otherwise, a ValueError will be raised.
        """
        if value is None or isinstance(value, str):
            return value
        if isinstance(value, UUID):
            return str(value)
        msg = f"The provided Session ID must be a UUID, string, or None. Got {value} of type {type(value)}."
        raise ValueError(msg)


# 数据输出响应模型：定义数据 API 返回的数据结构
class DataOutputResponse(BaseModel):
    """Data output response schema."""

    data: list[dict | None]


# 包含检查元类：为枚举类添加 in 运算符支持
class ContainsEnumMeta(enum.EnumMeta):
    def __contains__(cls, item) -> bool:
        try:
            cls(item)
        except ValueError:
            return False
        else:
            return True
