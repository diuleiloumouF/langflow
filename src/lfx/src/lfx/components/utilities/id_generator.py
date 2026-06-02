import uuid
from typing import Any

from typing_extensions import override

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output
from lfx.schema.dotdict import dotdict
from lfx.schema.message import Message


# ID 生成器组件，生成唯一的 UUID 标识符
class IDGeneratorComponent(Component):
    # 组件显示名称
    display_name = "ID Generator"
    # 组件描述信息
    description = "Generates a unique ID."
    # 组件图标
    icon = "fingerprint"
    # 组件内部名称
    name = "IDGenerator"
    # 标记为遗留组件
    legacy = True

    # 组件输入参数定义
    inputs = [
        MessageTextInput(
            name="unique_id",
            display_name="Value",
            info="The generated unique ID.",
            refresh_button=True,
            tool_mode=True,
        ),
    ]

    # 组件输出参数定义
    outputs = [
        Output(display_name="ID", name="id", method="generate_id"),
    ]

    # 更新构建配置，当字段值变化时重新生成 UUID
    @override
    def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        if field_name == "unique_id":
            build_config[field_name]["value"] = str(uuid.uuid4())
        return build_config

    # 生成唯一 ID 并返回 Message 对象
    def generate_id(self) -> Message:
        unique_id = self.unique_id or str(uuid.uuid4())
        self.status = f"Generated ID: {unique_id}"
        return Message(text=unique_id)
