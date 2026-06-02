import os

from mem0 import Memory, MemoryClient

from lfx.base.memory.model import LCChatMemoryComponent
from lfx.inputs.inputs import DictInput, HandleInput, MessageTextInput, NestedDictInput, SecretStrInput
from lfx.io import Output
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.utils.validate_cloud import raise_error_if_astra_cloud_disable_component

# Mem0 聊天记忆组件在 Astra 云环境中不可用时的提示信息
disable_component_in_astra_cloud_msg = (
    "Mem0 chat memory is not supported in Astra cloud environment. Please use local storage mode or mem0 cloud."
)


# Mem0 聊天记忆组件，基于 Mem0 记忆存储实现聊天消息的检索和存储
class Mem0MemoryComponent(LCChatMemoryComponent):
    display_name = "Mem0 Chat Memory"
    description = "Retrieves and stores chat messages using Mem0 memory storage."
    name = "mem0_chat_memory"
    icon: str = "Mem0"

    # 组件输入定义
    inputs = [
        # Mem0 配置字典，用于初始化 Mem0 记忆实例
        NestedDictInput(
            name="mem0_config",
            display_name="Mem0 Configuration",
            info="""Configuration dictionary for initializing Mem0 memory instance.
                    Example:
                    {
                        "graph_store": {
                            "provider": "neo4j",
                            "config": {
                                "url": "neo4j+s://your-neo4j-url",
                                "username": "neo4j",
                                "password": "your-password"
                            }
                        },
                        "version": "v1.1"
                    }""",
            input_types=["Data", "JSON"],
        ),
        # 待摄入的消息内容
        MessageTextInput(
            name="ingest_message",
            display_name="Message to Ingest",
            info="The message content to be ingested into Mem0 memory.",
        ),
        # 已有的 Mem0 记忆实例（可选），如果未提供则会创建新实例
        HandleInput(
            name="existing_memory",
            display_name="Existing Memory Instance",
            input_types=["Memory"],
            info="Optional existing Mem0 memory instance. If not provided, a new instance will be created.",
        ),
        # 与消息关联的用户标识符
        MessageTextInput(
            name="user_id", display_name="User ID", info="Identifier for the user associated with the messages."
        ),
        # 用于在 Mem0 中搜索相关记忆的查询文本
        MessageTextInput(
            name="search_query", display_name="Search Query", info="Input text for searching related memories in Mem0."
        ),
        # Mem0 平台的 API 密钥，留空则使用本地版本
        SecretStrInput(
            name="mem0_api_key",
            display_name="Mem0 API Key",
            info="API key for Mem0 platform. Leave empty to use the local version.",
        ),
        # 与摄入消息关联的额外元数据（高级选项）
        DictInput(
            name="metadata",
            display_name="Metadata",
            info="Additional metadata to associate with the ingested message.",
            advanced=True,
        ),
        # OpenAI API 密钥，使用 OpenAI Embeddings 且未提供配置时需要
        SecretStrInput(
            name="openai_api_key",
            display_name="OpenAI API Key",
            required=False,
            info="API key for OpenAI. Required if using OpenAI Embeddings without a provided configuration.",
        ),
    ]

    # 组件输出定义：记忆实例和搜索结果
    outputs = [
        # 输出记忆实例，通过 ingest_data 方法获取
        Output(name="memory", display_name="Mem0 Memory", method="ingest_data"),
        # 输出搜索结果，通过 build_search_results 方法获取
        Output(
            name="search_results",
            display_name="Search Results",
            method="build_search_results",
        ),
    ]

    # 根据提供的配置和 API 密钥构建 Mem0 记忆实例
    def build_mem0(self) -> Memory:
        """Initializes a Mem0 memory instance based on provided configuration and API keys."""
        # Check if we're in Astra cloud environment and raise an error if we are.
        raise_error_if_astra_cloud_disable_component(disable_component_in_astra_cloud_msg)

        # 如果提供了 OpenAI API 密钥，则将其设置到环境变量中
        if self.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.openai_api_key

        try:
            # 未提供 Mem0 API 密钥时，使用本地 Memory 实例
            if not self.mem0_api_key:
                return Memory.from_config(config_dict=dict(self.mem0_config)) if self.mem0_config else Memory()
            # 提供了 Mem0 API 密钥时，使用云端 MemoryClient
            if self.mem0_config:
                return MemoryClient.from_config(api_key=self.mem0_api_key, config_dict=dict(self.mem0_config))
            return MemoryClient(api_key=self.mem0_api_key)
        except ImportError as e:
            msg = "Mem0 is not properly installed. Please install it with 'pip install -U mem0ai'."
            raise ImportError(msg) from e

    # 将新消息摄入到 Mem0 记忆中并返回更新后的记忆实例
    def ingest_data(self) -> Memory:
        """Ingests a new message into Mem0 memory and returns the updated memory instance."""
        # Check if we're in Astra cloud environment and raise an error if we are.
        raise_error_if_astra_cloud_disable_component(disable_component_in_astra_cloud_msg)

        # 优先使用已有的记忆实例，否则构建新的实例
        mem0_memory = self.existing_memory or self.build_mem0()

        # 如果缺少摄入消息或用户 ID，则记录警告并直接返回
        if not self.ingest_message or not self.user_id:
            logger.warning("Missing 'ingest_message' or 'user_id'; cannot ingest data.")
            return mem0_memory

        metadata = self.metadata or {}

        logger.info("Ingesting message for user_id: %s", self.user_id)

        try:
            # 调用 Mem0 的 add 方法将消息添加到记忆存储中
            mem0_memory.add(self.ingest_message, user_id=self.user_id, metadata=metadata)
        except Exception:
            logger.exception("Failed to add message to Mem0 memory.")
            raise

        return mem0_memory

    # 根据搜索查询在 Mem0 记忆中检索相关消息并返回结果
    def build_search_results(self) -> Data:
        """Searches the Mem0 memory for related messages based on the search query and returns the results."""
        # Check if we're in Astra cloud environment and raise an error if we are.
        raise_error_if_astra_cloud_disable_component(disable_component_in_astra_cloud_msg)

        # 先执行数据摄入以确保记忆是最新的
        mem0_memory = self.ingest_data()
        search_query = self.search_query
        user_id = self.user_id

        logger.info("Search query: %s", search_query)

        try:
            if search_query:
                # 有搜索查询时，按查询内容和用户 ID 搜索相关记忆
                logger.info("Performing search with query.")
                related_memories = mem0_memory.search(query=search_query, filters={"user_id": user_id})
            else:
                # 无搜索查询时，获取该用户的所有记忆
                logger.info("Retrieving all memories for user_id: %s", user_id)
                related_memories = mem0_memory.get_all(filters={"user_id": user_id})
        except Exception:
            logger.exception("Failed to retrieve related memories from Mem0.")
            raise

        logger.info("Related memories retrieved: %s", related_memories)
        return related_memories
