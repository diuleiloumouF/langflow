# 枚举类型支持
from enum import Enum

# 类型注解支持
from typing import Any

# Pydantic 数据模型支持
from pydantic import BaseModel, Field, field_serializer, model_validator

# 项目内部模块：使用量统计、输出值/流URL定义、序列化工具、聊天输出响应等
from lfx.schema.properties import Usage
from lfx.schema.schema import OutputValue, StreamURL
from lfx.serialization.serialization import serialize
from lfx.utils.schemas import ChatOutputResponse, ContainsEnumMeta


class ResultData(BaseModel):
    """单个组件执行结果数据模型，用于存储组件运行后的输出、日志、消息等信息。"""

    # 组件的原始执行结果（如文本、JSON等）
    results: Any | None = Field(default_factory=dict)
    # 组件生成的产物（如文件、媒体等）
    artifacts: Any | None = Field(default_factory=dict)
    # 组件的标准化输出（包含消息内容和类型信息）
    outputs: dict | None = Field(default_factory=dict)
    # 组件执行过程中的日志信息
    logs: dict | None = Field(default_factory=dict)
    # 聊天输出响应消息列表
    messages: list[ChatOutputResponse] | None = Field(default_factory=list)
    # 执行耗时（秒）
    timedelta: float | None = None
    # 格式化的执行时长字符串
    duration: str | None = None
    # 组件的显示名称
    component_display_name: str | None = None
    # 组件的唯一标识符
    component_id: str | None = None
    # 是否使用了冻结的结果（缓存）
    used_frozen_result: bool | None = False
    # 本次执行的 token 使用量统计
    token_usage: Usage | None = None

    @field_serializer("results")
    def serialize_results(self, value):
        """序列化 results 字段，对字典中的每个值执行自定义序列化。"""
        if isinstance(value, dict):
            return {key: serialize(val) for key, val in value.items()}
        return serialize(value)

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values):
        """模型验证器：当 outputs 为空但 artifacts 存在时，自动从 artifacts 构建 outputs。"""
        if not values.get("outputs") and values.get("artifacts"):
            # Build the log from the artifacts
            # 遍历所有产物，将其转换为标准化输出格式

            for key in values["artifacts"]:
                message = values["artifacts"][key]

                # ! Temporary fix
                # 跳过空消息（临时修复方案）
                if message is None:
                    continue

                if "stream_url" in message and "type" in message:
                    # 处理流式 URL 类型的产物
                    stream_url = StreamURL(location=message["stream_url"])
                    values["outputs"].update({key: OutputValue(message=stream_url, type=message["type"])})
                elif "type" in message:
                    # 处理普通类型的消息产物
                    values["outputs"].update({key: OutputValue(message=message, type=message["type"])})
        return values


class InterfaceComponentTypes(str, Enum, metaclass=ContainsEnumMeta):
    """界面组件类型枚举，定义了所有可用的输入/输出组件类型。"""

    # 聊天输入组件
    ChatInput = "ChatInput"
    # 聊天输出组件
    ChatOutput = "ChatOutput"
    # 文本输入组件
    TextInput = "TextInput"
    # 文本输出组件
    TextOutput = "TextOutput"
    # 数据输出组件
    DataOutput = "DataOutput"
    # Webhook 输入组件
    WebhookInput = "Webhook"


# 聊天组件列表（ChatInput 和 ChatOutput）
CHAT_COMPONENTS = [InterfaceComponentTypes.ChatInput, InterfaceComponentTypes.ChatOutput]
# 记录类组件列表（DataOutput）
RECORDS_COMPONENTS = [InterfaceComponentTypes.DataOutput]
# 所有输入组件列表
INPUT_COMPONENTS = [
    InterfaceComponentTypes.ChatInput,
    InterfaceComponentTypes.WebhookInput,
    InterfaceComponentTypes.TextInput,
]
# 所有输出组件列表
OUTPUT_COMPONENTS = [
    InterfaceComponentTypes.ChatOutput,
    InterfaceComponentTypes.DataOutput,
    InterfaceComponentTypes.TextOutput,
]


class RunOutputs(BaseModel):
    """单次运行的输入输出数据模型，汇总一次流执行的所有输入和输出结果。"""

    # 运行时的输入参数（键值对形式）
    inputs: dict = Field(default_factory=dict)
    # 运行产生的所有输出结果列表（每个元素对应一个组件的 ResultData）
    outputs: list[ResultData | None] = Field(default_factory=list)
