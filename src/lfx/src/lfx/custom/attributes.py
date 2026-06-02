# 组件属性验证与类型转换模块
# 提供对组件属性（如 icon、display_name、beta 等）的验证和类型安全的取值函数

from collections.abc import Callable

import emoji

from lfx.log.logger import logger


def validate_icon(value: str):
    # we are going to use the emoji library to validate the emoji
    # emojis can be defined using the :emoji_name: syntax
    # 使用 emoji 库验证图标值
    # emoji 可以通过 :emoji_name: 语法定义

    # 如果值不以冒号开头也不以冒号结尾，说明是纯文本或图片路径，直接返回
    if not value.startswith(":") and not value.endswith(":"):
        return value
    if not value.startswith(":") or not value.endswith(":"):
        # emoji should have both starting and ending colons
        # so if one of them is missing, we will raise
        # emoji 格式必须同时包含起始和结束冒号，缺少任一冒号则抛出异常
        msg = f"Invalid emoji. {value} is not a valid emoji."
        raise ValueError(msg)

    # 尝试将 :emoji_name: 格式转换为实际的 emoji 字符
    emoji_value = emoji.emojize(value, variant="emoji_type")
    if value == emoji_value:
        # 如果转换后没有变化，说明 :emoji_name: 不是有效的 emoji 名称
        logger.warning(f"Invalid emoji. {value} is not a valid emoji.")
        return value
    return emoji_value


def getattr_return_str(value):
    """将属性值转换为字符串，空值返回空字符串"""
    return str(value) if value else ""


def getattr_return_bool(value):
    """将属性值转换为布尔类型，非布尔值返回 None"""
    if isinstance(value, bool):
        return value
    return None


def getattr_return_int(value):
    """将属性值转换为整数类型，非整数值返回 None"""
    if isinstance(value, int):
        return value
    return None


def getattr_return_list_of_str(value):
    """将属性值转换为字符串列表，非列表值返回空列表"""
    if isinstance(value, list):
        return [str(val) for val in value]
    return []


def getattr_return_list_of_object(value):
    """返回对象列表，非列表值返回空列表"""
    if isinstance(value, list):
        return value
    return []


def getattr_return_list_of_values_from_dict(value):
    """从字典中提取所有值并返回列表，非字典值返回空列表"""
    if isinstance(value, dict):
        return list(value.values())
    return []


def getattr_return_dict(value):
    """返回字典，非字典值返回空字典"""
    if isinstance(value, dict):
        return value
    return {}


# 属性名到验证/转换函数的映射表
# 用于组件属性的类型安全访问，根据属性名自动选择对应的处理函数
ATTR_FUNC_MAPPING: dict[str, Callable] = {
    "display_name": getattr_return_str,  # 显示名称
    "description": getattr_return_str,  # 组件描述
    "beta": getattr_return_bool,  # 是否为 Beta 版本
    "legacy": getattr_return_bool,  # 是否为遗留版本
    "replacement": getattr_return_list_of_str,  # 替代组件列表
    "documentation": getattr_return_str,  # 文档链接/内容
    "priority": getattr_return_int,  # 优先级
    "icon": validate_icon,  # 图标（支持 emoji）
    "minimized": getattr_return_bool,  # 是否默认最小化
    "frozen": getattr_return_bool,  # 是否已冻结（不可修改）
    "is_input": getattr_return_bool,  # 是否为输入组件
    "is_output": getattr_return_bool,  # 是否为输出组件
    "conditional_paths": getattr_return_list_of_str,  # 条件路径列表
    "_outputs_map": getattr_return_list_of_values_from_dict,  # 输出映射
    "_inputs": getattr_return_list_of_values_from_dict,  # 输入列表
    "outputs": getattr_return_list_of_object,  # 输出对象列表
    "inputs": getattr_return_list_of_object,  # 输入对象列表
    "metadata": getattr_return_dict,  # 元数据字典
    "tool_mode": getattr_return_bool,  # 是否为工具模式
}
