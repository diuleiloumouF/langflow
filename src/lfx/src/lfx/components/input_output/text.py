from typing import Any

from lfx.base.io.text import TextComponent
from lfx.io import BoolInput, MultilineInput, Output
from lfx.schema.message import Message


# 文本输入组件，用于获取用户文本输入
# Text input component for getting user text inputs
class TextInputComponent(TextComponent):
    display_name = "Text Input"
    description = "Get user text inputs."
    documentation: str = "https://docs.langflow.org/text-input-and-output"
    icon = "type"
    name = "TextInput"

    inputs = [
        MultilineInput(
            name="input_value",
            display_name="Text",
            info="Text to be passed as input.",
        ),
        BoolInput(
            name="use_global_variable",
            display_name="Use Global Variable",
            info="Enable to select from global variables (shows globe icon). Disables multiline editing.",
            value=False,
            advanced=True,
            real_time_refresh=True,
        ),
    ]
    outputs = [
        Output(display_name="Output Text", name="text", method="text_response"),
    ]

    # 根据字段更新动态更新构建配置
    def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        if field_name == "use_global_variable":
            if field_value:
                # Enable global variable mode: single-line with password masking and globe dropdown
                build_config["input_value"]["multiline"] = False
                build_config["input_value"]["password"] = True
            else:
                # Default mode: multiline text editing
                build_config["input_value"]["multiline"] = True
                build_config["input_value"]["password"] = False
        return build_config

    # 文本响应方法，将输入值包装为 Message 对象返回
    def text_response(self) -> Message:
        return Message(
            text=self.input_value,
        )
