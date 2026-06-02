from typing import TYPE_CHECKING, Any

# 输入类型相关的工具函数模块
# 提供输入类型的懒加载和实例化功能

if TYPE_CHECKING:
    from langflow.inputs.inputs import InputTypes, InputTypesMap
else:
    InputTypes = Any
    InputTypesMap = Any

# 懒加载的输入类型映射缓存，避免循环导入
_InputTypesMap: dict[str, type["InputTypes"]] | None = None


def get_input_types_map():
    """获取输入类型映射字典（懒加载）。

    返回 InputTypesMap 字典，该字典将输入类型名称映射到对应的类。
    使用懒加载模式，仅在首次调用时从 langflow.inputs.inputs 导入。

    Returns:
        dict[str, type[InputTypes]]: 输入类型名称到类型类的映射
    """
    global _InputTypesMap  # noqa: PLW0603
    if _InputTypesMap is None:
        from langflow.inputs.inputs import InputTypesMap

        _InputTypesMap = InputTypesMap
    return _InputTypesMap


def instantiate_input(input_type: str, data: dict) -> InputTypes:
    """根据输入类型名称实例化对应的输入对象。

    根据提供的 input_type 字符串从映射中查找对应的类，
    然后使用 data 字典中的参数创建该类的实例。

    Args:
        input_type: 输入类型名称，需要在 InputTypesMap 中存在
        data: 用于实例化输入对象的参数字典

    Returns:
        InputTypes: 实例化后的输入对象

    Raises:
        ValueError: 当 input_type 在映射中不存在时抛出
    """
    input_types_map = get_input_types_map()

    input_type_class = input_types_map.get(input_type)
    if "type" in data:
        # Replace with field_type
        # 将数据中的 "type" 字段重命名为 "field_type"，以匹配输入类的字段名
        data["field_type"] = data.pop("type")
    if input_type_class:
        return input_type_class(**data)
    msg = f"Invalid input type: {input_type}"
    raise ValueError(msg)
