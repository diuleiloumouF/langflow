from typing import Any

from pydantic import BaseModel, Field


# 类代码详情模型，用于存储解析后的类结构信息
class ClassCodeDetails(BaseModel):
    """A dataclass for storing details about a class."""

    # 类名
    name: str
    # 类的文档字符串
    doc: str | None = None
    # 父类列表
    bases: list
    # 类属性列表
    attributes: list
    # 方法列表
    methods: list
    # __init__ 方法的参数信息
    init: dict | None = Field(default_factory=dict)


# 可调用对象代码详情模型，用于存储解析后的函数/方法结构信息
class CallableCodeDetails(BaseModel):
    """A dataclass for storing details about a callable."""

    # 函数名
    name: str
    # 函数的文档字符串
    doc: str | None = None
    # 函数参数列表
    args: list
    # 函数体语句列表
    body: list
    # 返回类型注解
    return_type: Any | None = None
    # 是否包含 return 语句
    has_return: bool = False


# 占位类，用于表示缺失的默认值标记
class MissingDefault:
    """A class to represent a missing default value."""

    def __repr__(self) -> str:
        return "MISSING"
