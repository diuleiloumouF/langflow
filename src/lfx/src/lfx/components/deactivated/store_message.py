# 自定义组件基类、消息存储工具、消息模型
from lfx.custom.custom_component.custom_component import CustomComponent
from lfx.memory import aget_messages, astore_message
from lfx.schema.message import Message


# 消息存储组件，用于存储聊天消息（已弃用）
class StoreMessageComponent(CustomComponent):
    display_name = "Store Message"
    # 组件描述：存储聊天消息
    description = "Stores a chat message."
    name = "StoreMessage"

    # 构建配置
    def build_config(self):
        return {
            "message": {"display_name": "Message"},
        }

    async def build(
        self,
        message: Message,
    ) -> Message:
        flow_id = self.graph.flow_id if hasattr(self, "graph") else None
        await astore_message(message, flow_id=flow_id)
        self.status = await aget_messages()

        return message
