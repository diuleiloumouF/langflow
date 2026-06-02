"""JSON and Data classes for langflow - imports from lfx.

This maintains backward compatibility while using the lfx implementation.
JSON is the new base type; Data is an alias for backwards compatibility.
"""

# 从 lfx 模块导入 JSON 和 Data 类，保持向后兼容性
# JSON 是新的基础类型；Data 是为了向后兼容而保留的别名
from lfx.schema.data import JSON, Data, custom_serializer, serialize_data

__all__ = ["JSON", "Data", "custom_serializer", "serialize_data"]
