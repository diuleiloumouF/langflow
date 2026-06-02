from collections.abc import Generator
from enum import Enum

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.schema.encoders import CUSTOM_ENCODERS
from lfx.schema.message import Message
from lfx.serialization.serialization import serialize


class ArtifactType(str, Enum):
    """组件输出结果的类型枚举，用于区分不同类型的组件产出物。"""

    TEXT = "text"  # 文本类型
    DATA = "data"  # Data 数据类型
    OBJECT = "object"  # 字典/对象类型
    ARRAY = "array"  # 数组/列表类型
    STREAM = "stream"  # 流式输出类型（生成器）
    UNKNOWN = "unknown"  # 未知类型
    MESSAGE = "message"  # 消息类型
    RECORD = "record"  # 记录类型


def get_artifact_type(value, build_result=None) -> str:
    """根据传入值的类型，判断并返回对应的产物类型字符串。

    该函数使用模式匹配（match/case）对值进行类型检测，
    依次判断是否为 Message、Data、str、dict、list/DataFrame 等类型，
    并递归处理 Message 和 Data 的内部数据。

    Args:
        value: 组件构建的输出值，可以是任意类型。
        build_result: 可选的构建结果，若为 Generator 则判定为流式类型。

    Returns:
        对应的 ArtifactType 枚举值字符串。
    """
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
    # 若类型仍为 UNKNOWN，但 build_result 或 Message.text 是生成器，则判定为流式类型
    if result == ArtifactType.UNKNOWN and (
        (build_result and isinstance(build_result, Generator))
        or (isinstance(value, Message) and isinstance(value.text, Generator))
    ):
        result = ArtifactType.STREAM

    return result.value


def _to_list_of_dicts(raw):
    """将原始列表转换为字典列表，用于序列化为 JSON 格式。

    对列表中每个元素：若支持 dict() 或 model_dump() 方法，
    则调用 serialize 进行序列化；否则转为字符串。

    Args:
        raw: 原始列表数据。

    Returns:
        转换后的字典列表。
    """
    raw_ = []
    for item in raw:
        if hasattr(item, "dict") or hasattr(item, "model_dump"):
            raw_.append(serialize(item))
        else:
            raw_.append(str(item))
    return raw_


def post_process_raw(raw, artifact_type: str):
    """对组件输出的原始数据进行后处理，使其适合返回给前端。

    根据 artifact_type 执行不同的处理逻辑：
    - STREAM 类型：清空内容（流式数据不直接返回）
    - ARRAY 类型：将 DataFrame 或列表转为字典列表
    - UNKNOWN 类型：尝试通过 jsonable_encoder 编码，若失败则返回默认成功消息

    Args:
        raw: 组件输出的原始数据。
        artifact_type: 产物类型字符串。

    Returns:
        一个元组 (处理后的数据, 最终的产物类型字符串)。
    """
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
