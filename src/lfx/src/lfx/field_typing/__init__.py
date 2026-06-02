from typing import Any

# 延迟导入 - 除 __all__ 外，模块级别不导入任何内容

# 导出的公共 API 列表，定义本模块对外暴露的所有字段类型常量
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
    "Input",
    "LanguageModel",
    "NestedDict",
    "Object",
    "Output",
    "PromptTemplate",
    "RangeSpec",
    "Retriever",
    "Text",
    "TextSplitter",
    "Tool",
    "VectorStore",
]

# 来自 constants 模块的常量名称集合
# 用于在 __getattr__ 中判断属性是否应从 constants 模块延迟加载
_CONSTANTS_NAMES = {
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
    "Retriever",
    "Text",
    "TextSplitter",
    "Tool",
    "VectorStore",
}


def __getattr__(name: str) -> Any:
    """模块级别的延迟导入机制。

    当通过 module.Attribute 方式访问未在模块级别导入的属性时，
    Python 会调用此函数。根据属性名从对应的子模块中延迟导入，
    从而避免模块加载时的循环依赖和性能开销。

    Args:
        name: 被访问的属性名称

    Returns:
        对应的字段类型常量或类型类

    Raises:
        AttributeError: 当属性名不在已知的常量集合中时抛出
    """
    # "Input" 类型来自模板字段基础模块
    if name == "Input":
        from lfx.template.field.base import Input

        return Input
    if name == "Output":
        from lfx.template.field.base import Output

        return Output
    if name == "RangeSpec":
        from .range_spec import RangeSpec

        return RangeSpec
    if name in _CONSTANTS_NAMES:
        from . import constants

        return getattr(constants, name)

    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
