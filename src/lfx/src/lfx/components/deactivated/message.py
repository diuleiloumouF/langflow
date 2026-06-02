# 自定义组件基类、消息模型、常量定义
from lfx.custom.custom_component.custom_component import CustomComponent
from lfx.schema.message import Message
from lfx.utils.constants import MESSAGE_SENDER_AI, MESSAGE_SENDER_USER


# 消息创建组件，根据会话 ID 创建消息对象（已弃用）
class MessageComponent(CustomComponent):
    display_name = "Message"
    # 组件描述：给定会话 ID 创建消息对象
    description = "Creates a Message object given a Session ID."
    name = "Message"

    # 构建配置
    def build_config(self):
        return {
            "sender": {
                "options": [MESSAGE_SENDER_AI, MESSAGE_SENDER_USER],
                "display_name": "Sender Type",
            },
            "sender_name": {"display_name": "Sender Name"},
            "text": {"display_name": "Text"},
            "session_id": {
                "display_name": "Session ID",
                "info": "Session ID of the chat history.",
                "input_types": ["Message"],
            },
        }

    def build(
        self,
        sender: str = MESSAGE_SENDER_USER,
        sender_name: str | None = None,
        session_id: str | None = None,
        text: str = "",
    ) -> Message:
        flow_id = self.graph.flow_id if hasattr(self, "graph") else None
        message = Message(text=text, sender=sender, sender_name=sender_name, flow_id=flow_id, session_id=session_id)

        self.status = message
        return message
