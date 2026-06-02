# 流程控制组件：消息透传
# 该组件用于将输入消息原样转发到输出，不做任何修改。
# 属于遗留组件，推荐使用 logic.ConditionalRouter 替代。

from lfx.custom.custom_component.component import Component
from lfx.io import MessageInput
from lfx.schema.message import Message
from lfx.template.field.base import Output


# 消息透传组件：直接将输入消息原样输出，常用于流程中需要保留消息的场景
class PassMessageComponent(Component):
    # 组件显示名称
    display_name = "Pass"
    # 组件描述：原样转发输入消息
    description = "Forwards the input message, unchanged."
    # 组件内部名称
    name = "Pass"
    # 组件图标
    icon = "arrow-right"
    # 标记为遗留组件，不推荐在新流程中使用
    legacy: bool = True
    # 建议的替代组件：逻辑条件路由器
    replacement = ["logic.ConditionalRouter"]

    # 组件输入参数定义
    inputs = [
        # 主输入消息：需要被透传的消息
        MessageInput(
            name="input_message",
            display_name="Input Message",
            info="The message to be passed forward.",
            required=True,
        ),
        # 被忽略的第二条消息：用于兼容性处理的临时方案，可忽略
        MessageInput(
            name="ignored_message",
            display_name="Ignored Message",
            info="A second message to be ignored. Used as a workaround for continuity.",
            advanced=True,
        ),
    ]

    # 组件输出定义：输出透传后的消息
    outputs = [
        Output(display_name="Output Message", name="output_message", method="pass_message"),
    ]

    # 消息透传方法：将输入消息原样作为输出返回
    def pass_message(self) -> Message:
        # 将输入消息设置为组件状态，便于在流程中查看
        self.status = self.input_message
        # 原样返回输入消息
        return self.input_message
