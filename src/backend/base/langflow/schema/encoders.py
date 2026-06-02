# 自定义 JSON 编码器模块
# 为 FastAPI 的 jsonable_encoder 提供自定义类型编码支持
from collections.abc import Callable
from datetime import datetime


# 将可调用对象（函数/方法）编码为字符串（优先使用函数名）
def encode_callable(obj: Callable):
    return obj.__name__ if hasattr(obj, "__name__") else str(obj)


# 将 datetime 对象编码为标准化的字符串格式
def encode_datetime(obj: datetime):
    return obj.strftime("%Y-%m-%d %H:%M:%S %Z")


# 自定义编码器映射表：类型 -> 编码函数
CUSTOM_ENCODERS = {Callable: encode_callable, datetime: encode_datetime}
