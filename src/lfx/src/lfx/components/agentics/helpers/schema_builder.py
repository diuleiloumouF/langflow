# 将字段定义转换为 Pydantic 模型的 Schema 构建工具模块
"""Schema building utilities for converting field definitions to Pydantic models."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


# 将字段定义转换为 Pydantic 模型创建所需的 schema 元组列表
def build_schema_fields(fields: list[dict[str, Any]]) -> list[tuple[str, str, str, bool]]:
    """Convert field definitions to schema tuples for Pydantic model creation.

    Transforms user-defined field specifications into the format required by
    the Agentics framework's create_pydantic_model function. Handles list types
    by wrapping the base type in list[] notation.

    Args:
        fields: List of field dictionaries, each containing:
            - name: Field name
            - description: Field description
            - type: Base data type (str, int, float, bool, dict)
            - multiple: Whether this field should be a list of the type

    Returns:
        List of tuples in format (name, description, type_str, required) where:
        - name: Field name
        - description: Field description
        - type_str: Type string, potentially wrapped as "list[type]" if multiple=True
        - required: Always False (fields are optional by default)
    """
    # 将每个字段字典转换为 (名称, 描述, 类型字符串, 是否必填) 的元组
    return [
        (
            field["name"],
            field["description"],
            # 如果 multiple 为 True，则将基础类型包装为 list[type] 形式
            field["type"] if not field["multiple"] else f"list[{field['type']}]",
            False,
        )
        for field in fields
    ]
