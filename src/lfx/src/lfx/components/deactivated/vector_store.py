# LangChain 向量存储检索器
from langchain_core.vectorstores import VectorStoreRetriever

# 自定义组件基类、类型定义、输入组件
from lfx.custom.custom_component.custom_component import CustomComponent
from lfx.field_typing import VectorStore
from lfx.inputs.inputs import HandleInput


# 向量存储检索器组件，将向量存储转换为检索器（已弃用）
class VectorStoreRetrieverComponent(CustomComponent):
    display_name = "VectorStore Retriever"
    # 组件描述：向量存储检索器
    description = "A vector store retriever"
    name = "VectorStoreRetriever"
    icon = "LangChain"

    # 输入参数定义
    inputs = [
        # 向量存储连接
        HandleInput(
            name="vectorstore",
            display_name="Vector Store",
            input_types=["VectorStore"],
            required=True,
        ),
    ]

    # 构建向量存储检索器实例
    def build(self, vectorstore: VectorStore) -> VectorStoreRetriever:
        return vectorstore.as_retriever()
