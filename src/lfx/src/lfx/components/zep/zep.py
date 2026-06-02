# Zep 聊天记忆组件，通过 Zep 服务检索和存储聊天消息历史
from lfx.base.memory.model import LCChatMemoryComponent
from lfx.field_typing.constants import Memory
from lfx.inputs.inputs import DropdownInput, MessageTextInput, SecretStrInput


# Zep 聊天记忆组件，提供聊天消息的持久化存储和检索（已标记为遗留组件）
class ZepChatMemory(LCChatMemoryComponent):
    # 组件显示名称
    display_name = "Zep Chat Memory"
    # 组件描述
    description = "Retrieves and store chat messages from Zep."
    # 组件内部名称
    name = "ZepChatMemory"
    # 组件图标
    icon = "ZepMemory"
    # 标记为遗留组件，建议使用新的替代方案
    legacy = True
    # 推荐的替代组件
    replacement = ["helpers.Memory"]

    # 组件输入参数定义
    inputs = [
        # Zep 服务实例 URL 地址
        MessageTextInput(name="url", display_name="Zep URL", info="URL of the Zep instance."),
        # Zep API 密钥
        SecretStrInput(name="api_key", display_name="Zep API Key", info="API Key for the Zep instance."),
        # API 基础路径，本地实例使用 v1，云版本使用 v2
        DropdownInput(
            name="api_base_path",
            display_name="API Base Path",
            options=["api/v1", "api/v2"],
            value="api/v1",
            advanced=True,
        ),
        # 会话 ID，用于区分不同的聊天会话
        MessageTextInput(
            name="session_id", display_name="Session ID", info="Session ID for the message.", advanced=True
        ),
    ]

    # 构建聊天消息历史实例
    def build_message_history(self) -> Memory:
        try:
            # Monkeypatch API_BASE_PATH to
            # avoid 404
            # This is a workaround for the local Zep instance
            # cloud Zep works with v2
            # 修补 API_BASE_PATH 以避免本地 Zep 实例返回 404 错误
            import zep_python.zep_client
            from zep_python import ZepClient
            from zep_python.langchain import ZepChatMessageHistory

            zep_python.zep_client.API_BASE_PATH = self.api_base_path
        except ImportError as e:
            msg = "Could not import zep-python package. Please install it with `pip install zep-python`."
            raise ImportError(msg) from e

        # 创建 Zep 客户端并返回聊天消息历史对象
        zep_client = ZepClient(api_url=self.url, api_key=self.api_key)
        return ZepChatMessageHistory(session_id=self.session_id, zep_client=zep_client)
