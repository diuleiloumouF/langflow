from typing import Any, TypedDict

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, create_model

# 表示布尔真值的字符串列表，用于将字符串转换为布尔值
TRUE_VALUES = ["true", "1", "t", "y", "yes"]


# 模式字段的类型定义，用于描述动态模型中的字段信息
class SchemaField(TypedDict):
    name: str
    type: str
    description: str
    multiple: bool


# 基础模型类，继承自 Pydantic BaseModel，允许通过字段名进行赋值
class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(populate_by_name=True)


# 类型字符串到 Python 类型的映射
def _get_type_annotation(type_str: str, *, multiple: bool) -> type:
    type_mapping = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "boolean": bool,
        "list": list[Any],
        "dict": dict[str, Any],
        "number": float,
        "text": str,
    }
    # 获取基础类型，如果类型字符串无效则抛出异常
    try:
        base_type = type_mapping[type_str]
    except KeyError as e:
        msg = f"Invalid type: {type_str}"
        raise ValueError(msg) from e
    # 如果是多值字段，返回列表类型
    if multiple:
        return list[base_type]  # type: ignore[valid-type]
    return base_type  # type: ignore[return-value]


# 根据模式定义动态构建 Pydantic 模型
def build_model_from_schema(schema: list[SchemaField]) -> type[PydanticBaseModel]:
    fields = {}
    # 遍历模式中的每个字段定义
    for field in schema:
        field_name = field["name"]
        field_type_str = field["type"]
        description = field.get("description", "")
        # 获取是否为多值字段，默认为 False
        multiple = field.get("multiple", False)
        multiple = coalesce_bool(multiple)
        # 获取字段的类型注解
        field_type_annotation = _get_type_annotation(field_type_str, multiple=multiple)
        # 将字段信息添加到字段字典中，包含类型和描述
        fields[field_name] = (field_type_annotation, Field(description=description))
    # 使用 create_model 动态创建名为 "OutputModel" 的模型类
    return create_model("OutputModel", **fields)


# 将给定值转换为布尔值的函数
def coalesce_bool(value: Any) -> bool:
    """Coalesces the given value into a boolean.

    Args:
        value (Any): The value to be coalesced.

    Returns:
        bool: The coalesced boolean value.

    """
    # 如果已经是布尔值，直接返回
    if isinstance(value, bool):
        return value
    # 如果是字符串，检查是否在真值列表中
    if isinstance(value, str):
        return value.lower() in TRUE_VALUES
    # 如果是整数，使用 bool() 转换
    if isinstance(value, int):
        return bool(value)
    # 其他类型默认返回 False
    return False
