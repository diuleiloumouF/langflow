# 聊天记忆组件基类、类型定义、输入组件
from lfx.base.memory.model import LCChatMemoryComponent
from lfx.field_typing.constants import Memory
from lfx.inputs.inputs import DictInput, MessageTextInput, SecretStrInput


# Cassandra 聊天记忆组件，用于从 Apache Cassandra 检索和存储聊天消息
class CassandraChatMemory(LCChatMemoryComponent):
    display_name = "Cassandra Chat Memory"
    # 组件描述：从 Apache Cassandra 检索和存储聊天消息
    description = "Retrieves and store chat messages from Apache Cassandra."
    name = "CassandraChatMemory"
    icon = "Cassandra"

    # 输入参数定义
    inputs = [
        # 数据库连接点或 Astra DB 数据库 ID
        MessageTextInput(
            name="database_ref",
            display_name="Contact Points / Astra Database ID",
            info="Contact points for the database (or Astra DB database ID)",
            required=True,
        ),
        # 数据库用户名（Astra DB 可留空）
        MessageTextInput(
            name="username", display_name="Username", info="Username for the database (leave empty for Astra DB)."
        ),
        # 数据库密码或 Astra DB Token
        SecretStrInput(
            name="token",
            display_name="Password / Astra DB Token",
            info="User password for the database (or Astra DB token).",
            required=True,
        ),
        # 键空间（Astra DB 命名空间）
        MessageTextInput(
            name="keyspace",
            display_name="Keyspace",
            info="Table Keyspace (or Astra DB namespace).",
            required=True,
        ),
        # 表名（Astra DB 集合名称）
        MessageTextInput(
            name="table_name",
            display_name="Table Name",
            info="The name of the table (or Astra DB collection) where vectors will be stored.",
            required=True,
        ),
        # 会话 ID，用于区分不同的聊天会话
        MessageTextInput(
            name="session_id", display_name="Session ID", info="Session ID for the message.", advanced=True
        ),
        # Cassandra 集群额外参数
        DictInput(
            name="cluster_kwargs",
            display_name="Cluster arguments",
            info="Optional dictionary of additional keyword arguments for the Cassandra cluster.",
            advanced=True,
            is_list=True,
        ),
    ]

    # 构建聊天消息历史记录实例
    def build_message_history(self) -> Memory:
        from langchain_community.chat_message_histories import CassandraChatMessageHistory

        try:
            import cassio
        except ImportError as e:
            msg = "Could not import cassio integration package. Please install it with `pip install cassio`."
            raise ImportError(msg) from e

        from uuid import UUID

        database_ref = self.database_ref

        try:
            UUID(self.database_ref)
            is_astra = True
        except ValueError:
            is_astra = False
            if "," in self.database_ref:
                # use a copy because we can't change the type of the parameter
                database_ref = self.database_ref.split(",")

        if is_astra:
            cassio.init(
                database_id=database_ref,
                token=self.token,
                cluster_kwargs=self.cluster_kwargs,
            )
        else:
            cassio.init(
                contact_points=database_ref,
                username=self.username,
                password=self.token,
                cluster_kwargs=self.cluster_kwargs,
            )

        return CassandraChatMessageHistory(
            session_id=self.session_id,
            table_name=self.table_name,
            keyspace=self.keyspace,
        )
