from urllib import parse

from langchain_community.chat_message_histories.redis import RedisChatMessageHistory

from lfx.base.memory.model import LCChatMemoryComponent
from lfx.field_typing.constants import Memory
from lfx.inputs.inputs import IntInput, MessageTextInput, SecretStrInput, StrInput


# Redis 聊天记忆组件，从 Redis 检索和存储聊天消息
class RedisIndexChatMemory(LCChatMemoryComponent):
    # 组件显示名称
    display_name = "Redis Chat Memory"
    # 组件描述信息
    description = "Retrieves and store chat messages from Redis."
    # 组件内部名称
    name = "RedisChatMemory"
    # 组件图标
    icon = "Redis"

    # 组件输入参数定义
    inputs = [
        StrInput(
            name="host", display_name="hostname", required=True, value="localhost", info="IP address or hostname."
        ),
        IntInput(name="port", display_name="port", required=True, value=6379, info="Redis Port Number."),
        StrInput(name="database", display_name="database", required=True, value="0", info="Redis database."),
        MessageTextInput(
            name="username", display_name="Username", value="", info="The Redis user name.", advanced=True
        ),
        SecretStrInput(
            name="password", display_name="Redis Password", value="", info="The password for username.", advanced=True
        ),
        StrInput(name="key_prefix", display_name="Key prefix", info="Key prefix.", advanced=True),
        MessageTextInput(
            name="session_id", display_name="Session ID", info="Session ID for the message.", advanced=True
        ),
    ]

    # 构建 Redis 聊天消息历史记录实例
    def build_message_history(self) -> Memory:
        kwargs = {}
        password: str | None = self.password
        if self.key_prefix:
            kwargs["key_prefix"] = self.key_prefix
        if password:
            password = parse.quote_plus(password)

        url = f"redis://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        return RedisChatMessageHistory(session_id=self.session_id, url=url, **kwargs)
