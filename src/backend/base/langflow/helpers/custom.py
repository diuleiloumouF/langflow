from typing import Any


# 格式化类型对象，将其转换为可读的字符串形式
def format_type(type_: Any) -> str:
    # 如果类型是 str，返回友好的显示名称 "Text"
    if type_ is str:
        type_ = "Text"
    # 如果类型有 __name__ 属性（如内置类型、自定义类），使用其名称
    elif hasattr(type_, "__name__"):
        type_ = type_.__name__
    # 如果类型有 __class__ 属性（如类的实例），使用其所属类的名称
    elif hasattr(type_, "__class__"):
        type_ = type_.__class__.__name__
    # 兜底处理：直接将类型转换为字符串
    else:
        type_ = str(type_)
    return type_
