# Re-export everything from lfx.field_typing.constants for backward compatibility
# 从 lfx.field_typing.constants 重新导出所有内容，用于向后兼容
# Import additional types
# 导入额外的类型
from collections.abc import Callable
from typing import Text

# 导入 lfx 中定义的所有字段类型常量
from lfx.field_typing.constants import (
    # 自定义组件支持的所有类型映射
    CUSTOM_COMPONENT_SUPPORTED_TYPES,
    # LangChain 组件的默认导入语句
    DEFAULT_IMPORT_STRING,
    # LangChain 基础类型的集合
    LANGCHAIN_BASE_TYPES,
    # Import all the langchain types that may be needed
    # 导入所有可能需要的 LangChain 类型
    AgentExecutor,
    BaseChatMemory,
    BaseChatMessageHistory,
    BaseChatModel,
    BaseDocumentCompressor,
    BaseLanguageModel,
    BaseLLM,
    BaseLLMOutputParser,
    BaseLoader,
    BaseMemory,
    BaseOutputParser,
    BasePromptTemplate,
    BaseRetriever,
    BaseTool,
    Chain,
    ChatPromptTemplate,
    Code,
    Document,
    Embeddings,
    LanguageModel,
    Memory,
    NestedDict,
    Object,
    OutputParser,
    PromptTemplate,
    Retriever,
    TextSplitter,
    Tool,
    ToolEnabledLanguageModel,
    VectorStore,
    VectorStoreRetriever,
)

# Import lfx schema types
# 导入 lfx 模式类型
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame

# Import Message from langflow.schema for backward compatibility
# 从 langflow.schema 导入 Message，用于向后兼容
from langflow.schema.message import Message

# Add Message and DataFrame to CUSTOM_COMPONENT_SUPPORTED_TYPES
# 将 Message 和 DataFrame 添加到自定义组件支持类型映射中
CUSTOM_COMPONENT_SUPPORTED_TYPES = {
    **CUSTOM_COMPONENT_SUPPORTED_TYPES,
    "Message": Message,
    "DataFrame": DataFrame,
}

# 模块公开导出的所有类型名称
__all__ = [
    "CUSTOM_COMPONENT_SUPPORTED_TYPES",
    "DEFAULT_IMPORT_STRING",
    "LANGCHAIN_BASE_TYPES",
    # Langchain types
    # LangChain 核心类型
    "AgentExecutor",
    "BaseChatMemory",
    "BaseChatMessageHistory",
    "BaseChatModel",
    "BaseDocumentCompressor",
    "BaseLLM",
    "BaseLLMOutputParser",
    "BaseLanguageModel",
    "BaseLoader",
    "BaseMemory",
    "BaseOutputParser",
    "BasePromptTemplate",
    "BaseRetriever",
    "BaseTool",
    # Additional types
    # 额外类型
    "Callable",
    "Chain",
    "ChatPromptTemplate",
    "Code",
    "Data",
    "DataFrame",
    "Document",
    "Embeddings",
    "LanguageModel",
    "Memory",
    "Message",
    "NestedDict",
    "Object",
    "OutputParser",
    "PromptTemplate",
    "Retriever",
    "Text",
    "TextSplitter",
    "Tool",
    "ToolEnabledLanguageModel",
    "VectorStore",
    "VectorStoreRetriever",
]
