"""跨模块 BaseModel，用于处理重新导出的类。

该模块提供了一个元类和基础模型，使 isinstance 检查能够在 Pydantic 模型的
模块边界之间正常工作。当同一个类从不同模块重新导出时（例如 lfx.Message 与
langflow.schema.Message），由于 Python 的 isinstance() 检查因模块路径不同而
失败，此模块非常有用。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# 跨模块元类，继承自 Pydantic BaseModel 的元类
class CrossModuleMeta(type(BaseModel)):  # type: ignore[misc]
    """支持跨模块 isinstance 检查的 Pydantic 元类。

    该元类重写 __instancecheck__，基于模型的字段进行结构化类型检查，
    而非严格的类标识检查。这允许来自不同模块路径的同一模型实例被识别为兼容。
    """

    def __instancecheck__(cls, instance: Any) -> bool:
        """检查实例是否与该类跨模块兼容。

        首先执行标准 isinstance 检查。如果失败，则回退到检查实例是否具有
        所有必需的 Pydantic 模型属性和兼容的模型字段集。

        Args:
            instance: 要检查的对象。

        Returns:
            bool: 如果实例与该类兼容则返回 True。
        """
        # 首先尝试标准 isinstance 检查
        if type.__instancecheck__(cls, instance):
            return True

        # 如果失败，则检查跨模块兼容性
        # 一个对象跨模块兼容的条件是：
        # 1. 具有 model_fields 属性（是 Pydantic 模型）
        # 2. 具有相同的 __class__.__name__
        # 3. 具有兼容的模型字段
        if not hasattr(instance, "model_fields"):
            return False

        # 检查类名是否匹配
        if instance.__class__.__name__ != cls.__name__:
            return False

        # 检查实例是否具有 cls 的所有必需字段
        cls_fields = set(cls.model_fields.keys()) if hasattr(cls, "model_fields") else set()
        instance_fields = set(type(instance).model_fields.keys())

        # 实例必须至少具有与该类相同的字段
        # （可以有更多字段，但不能缺少必需字段）
        return cls_fields.issubset(instance_fields)


# 带有跨模块 isinstance 支持的 Pydantic 基础模型
class CrossModuleModel(BaseModel, metaclass=CrossModuleMeta):
    """支持跨模块 isinstance 检查的 Pydantic 基础模型。

    该类应作为可能从不同模块重新导出的模型的基类。通过使用结构化类型检查，
    它使 isinstance() 检查能够在模块边界之间正常工作。

    Example:
        >>> class Message(CrossModuleModel):
        ...     text: str
        ...
        >>> # 即使 Message 从不同路径导入：
        >>> from lfx.schema.message import Message as LfxMessage
        >>> from langflow.schema import Message as LangflowMessage
        >>> msg = LfxMessage(text="hello")
        >>> isinstance(msg, LangflowMessage)  # True（通过跨模块支持）
    """
