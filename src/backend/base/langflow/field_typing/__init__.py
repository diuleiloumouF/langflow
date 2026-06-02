"""字段类型模块。

提供 Langflow 组件中常用的字段类型定义，包括语言模型、记忆、检索器、
提示模板、向量存储等类型别名，以及 Input/Output 组件和 RangeSpec 规格。
通过 __getattr__ 实现延迟导入，避免循环依赖问题。
"""

from typing import Any

# 从 lfx.field_typing.constants 导入所有字段类型别名
from lfx.field_typing.constants import (
    AgentExecutor,
    BaseChatMemory,
    BaseChatModel,
    BaseDocumentCompressor,
    BaseLanguageModel,
    BaseLLM,
    BaseLoader,
    BaseMemory,
    BaseOutputParser,
    BasePromptTemplate,
    BaseRetriever,
    Callable,
    Chain,
    ChatPromptTemplate,
    Code,
    Data,
    Document,
    Embeddings,
    LanguageModel,
    NestedDict,
    Object,
    PromptTemplate,
    Retriever,
    Text,
    TextSplitter,
    Tool,
    VectorStore,
)

# 范围规格类型，用于定义数值型组件参数的取值范围
from lfx.field_typing.range_spec import RangeSpec


def _import_input_class():
    """延迟导入 Input 类，避免循环依赖。"""
    from lfx.template.field.base import Input

    return Input


def _import_output_class():
    """延迟导入 Output 类，避免循环依赖。"""
    from lfx.template.field.base import Output

    return Output


def __getattr__(name: str) -> Any:
    # This is to avoid circular imports
    # 通过自定义 __getattr__ 实现按需导入，避免模块加载时的循环引用
    if name == "Input":
        return _import_input_class()
    if name == "Output":
        return _import_output_class()
    if name == "RangeSpec":
        return RangeSpec
    # The other names should work as if they were imported from constants
    # Import the constants module langflow.field_typing.constants
    # 其余名称委托给 constants 模块处理，行为等同于从 constants 直接导入
    from . import constants

    return getattr(constants, name)


# 模块公开导出的符号列表
__all__ = [
    "AgentExecutor",
    "BaseChatMemory",
    "BaseChatModel",
    "BaseDocumentCompressor",
    "BaseLLM",
    "BaseLanguageModel",
    "BaseLoader",
    "BaseMemory",
    "BaseOutputParser",
    "BasePromptTemplate",
    "BaseRetriever",
    "Callable",
    "Chain",
    "ChatPromptTemplate",
    "Code",
    "Data",
    "Document",
    "Embeddings",
    "LanguageModel",
    "NestedDict",
    "Object",
    "PromptTemplate",
    "RangeSpec",
    "Retriever",
    "Text",
    "TextSplitter",
    "Tool",
    "VectorStore",
]
