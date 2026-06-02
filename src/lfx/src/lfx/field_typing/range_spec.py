"""Range specification for field types copied from langflow for lfx package / 字段类型的范围规格定义."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


# 范围规格模型类，用于定义数值字段的取值范围和步进参数
class RangeSpec(BaseModel):
    # 步进类型，支持 "int"（整数）或 "float"（浮点数），默认为 "float"
    step_type: Literal["int", "float"] = "float"
    # 最小值，默认为 -1.0
    min: float = -1.0
    # 最大值，默认为 1.0
    max: float = 1.0
    # 步进值（间隔），默认为 0.1
    step: float = 0.1

    # 验证器：确保最大值大于最小值
    @field_validator("max")
    @classmethod
    def max_must_be_greater_than_min(cls, v, values):
        if "min" in values.data and v <= values.data["min"]:
            msg = "Max must be greater than min"
            raise ValueError(msg)
        return v

    # 验证器：确保步进值为正数，且在整数步进类型下必须为整数
    @field_validator("step")
    @classmethod
    def step_must_be_positive(cls, v, values):
        if v <= 0:
            msg = "Step must be positive"
            raise ValueError(msg)
        if values.data["step_type"] == "int" and isinstance(v, float) and not v.is_integer():
            msg = "When step_type is int, step must be an integer"
            raise ValueError(msg)
        return v

    # 类方法：根据指定的步进类型创建一个新的 RangeSpec 实例
    @classmethod
    def set_step_type(cls, step_type: Literal["int", "float"], range_spec: RangeSpec) -> RangeSpec:
        return cls(min=range_spec.min, max=range_spec.max, step=range_spec.step, step_type=step_type)
