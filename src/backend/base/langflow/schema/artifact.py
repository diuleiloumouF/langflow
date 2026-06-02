# 工件类型枚举和后处理工具函数
# 用于在组件输出返回给前端之前，对构建结果进行分类和序列化处理
from collections.abc import Generator
from enum import Enum

from fastapi.encoders import jsonable_encoder
from lfx.log.logger import logger
from pydantic import BaseModel

from langflow.schema.data import Data
from langflow.schema.dataframe import DataFrame
from langflow.schema.encoders import CUSTOM_ENCODERS
from langflow.schema.message import Message
from langflow.serialization.serialization import serialize


# 工件类型枚举，用于标识组件输出结果的数据类型
class ArtifactType(str, Enum):
    TEXT = "text"  # 文本类型
    DATA = "data"  # Data 对象类型
    OBJECT = "object"  # 字典/对象类型
    ARRAY = "array"  # 列表/数组类型
    STREAM = "stream"  # 流式输出类型
    UNKNOWN = "unknown"  # 未知类型
    MESSAGE = "message"  # 消息类型


# 根据值的类型判断工件类型
def get_artifact_type(value, build_result=None) -> str:
    result = ArtifactType.UNKNOWN
    match value:
        case Message():
            if not isinstance(value.text, str):
                enum_value = get_artifact_type(value.text)
                result = ArtifactType(enum_value)
            else:
                result = ArtifactType.MESSAGE
        case Data():
            enum_value = get_artifact_type(value.data)
            result = ArtifactType(enum_value)

        case str():
            result = ArtifactType.TEXT

        case dict():
            result = ArtifactType.OBJECT

        case list() | DataFrame():
            result = ArtifactType.ARRAY
    if result == ArtifactType.UNKNOWN and (
        (build_result and isinstance(build_result, Generator))
        or (isinstance(value, Message) and isinstance(value.text, Generator))
    ):
        result = ArtifactType.STREAM

    return result.value


# 将原始列表转换为字典列表（可序列化的格式）
def _to_list_of_dicts(raw):
    raw_ = []
    for item in raw:
        if hasattr(item, "dict") or hasattr(item, "model_dump"):
            raw_.append(serialize(item))
        else:
            raw_.append(str(item))
    return raw_


# 对原始输出进行后处理，根据工件类型进行序列化和格式化
def post_process_raw(raw, artifact_type: str):
    default_message = "Built Successfully ✨"

    if artifact_type == ArtifactType.STREAM.value:
        raw = ""
    elif artifact_type == ArtifactType.ARRAY.value:
        raw = raw.to_dict(orient="records") if isinstance(raw, DataFrame) else _to_list_of_dicts(raw)
    elif artifact_type == ArtifactType.UNKNOWN.value and raw is not None:
        if isinstance(raw, BaseModel | dict):
            try:
                raw = jsonable_encoder(raw, custom_encoder=CUSTOM_ENCODERS)
                artifact_type = ArtifactType.OBJECT.value
            except Exception:  # noqa: BLE001
                logger.debug(f"Error converting to json: {raw} ({type(raw)})", exc_info=True)
                raw = default_message
        else:
            raw = default_message
    return raw, artifact_type
