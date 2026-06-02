# AstraDB 基础组件、聊天记忆组件基类、类型定义、输入组件
from lfx.base.datastax.astradb_base import AstraDBBaseComponent
from lfx.base.memory.model import LCChatMemoryComponent
from lfx.field_typing.constants import Memory
from lfx.inputs.inputs import MessageTextInput


# Astra DB 聊天记忆组件，用于从 Astra DB 检索和存储聊天消息
class AstraDBChatMemory(AstraDBBaseComponent, LCChatMemoryComponent):
    display_name = "Astra DB Chat Memory"
    # 组件描述：从 Astra DB 检索和存储聊天消息
    description = "Retrieves and stores chat messages from Astra DB."
    name = "AstraDBChatMemory"
    icon: str = "AstraDB"

    # 输入参数定义（继承 AstraDB 基础输入 + 会话 ID）
    inputs = [
        *AstraDBBaseComponent.inputs,
        # 会话 ID，用于区分不同的聊天会话
        MessageTextInput(
            name="session_id",
            display_name="Session ID",
            info="The session ID of the chat. If empty, the current session ID parameter will be used.",
            advanced=True,
        ),
    ]

    # 构建聊天消息历史记录实例
    def build_message_history(self) -> Memory:
        try:
            from langchain_astradb.chat_message_histories import AstraDBChatMessageHistory
        except ImportError as e:
            msg = (
                "Could not import langchain Astra DB integration package. "
                "Please install it with `uv pip install langchain-astradb`."
            )
            raise ImportError(msg) from e

        return AstraDBChatMessageHistory(
            session_id=self.session_id,
            collection_name=self.collection_name,
            token=self.token,
            api_endpoint=self.get_api_endpoint(),
            namespace=self.get_keyspace(),
            environment=self.environment,
        )
