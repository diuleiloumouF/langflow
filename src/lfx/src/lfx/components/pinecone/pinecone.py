# 数值计算库，用于浮点类型转换
import numpy as np

# LangChain 向量存储基类
from langchain_core.vectorstores import VectorStore

# 向量存储组件基类和缓存装饰器
from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store

# 文档转数据工具函数
from lfx.helpers.data import docs_to_data

# Langflow 输入组件
from lfx.io import DropdownInput, HandleInput, IntInput, SecretStrInput, StrInput

# Langflow 数据模型
from lfx.schema.data import Data


# Pinecone 向量存储组件，用于连接 Pinecone 向量数据库并提供文档搜索能力
class PineconeVectorStoreComponent(LCVectorStoreComponent):
    # 组件显示名称
    display_name = "Pinecone"
    # 组件描述
    description = "Pinecone Vector Store with search capabilities"
    # 组件内部名称
    name = "Pinecone"
    # 组件图标
    icon = "Pinecone"
    # 组件输入参数定义
    inputs = [
        # 索引名称，Pinecone 中的索引标识
        StrInput(name="index_name", display_name="Index Name", required=True),
        # 命名空间，用于隔离同一索引中的不同数据集
        StrInput(name="namespace", display_name="Namespace", info="Namespace for the index."),
        # 距离策略下拉菜单，决定向量相似度计算方式
        DropdownInput(
            name="distance_strategy",
            display_name="Distance Strategy",
            options=["Cosine", "Euclidean", "Dot Product"],
            value="Cosine",
            advanced=True,
        ),
        # Pinecone API 密钥，用于身份验证
        SecretStrInput(name="pinecone_api_key", display_name="Pinecone API Key", required=True),
        # 文本字段键名，指定记录中用作文本内容的字段
        StrInput(
            name="text_key",
            display_name="Text Key",
            info="Key in the record to use as text.",
            value="text",
            advanced=True,
        ),
        # 继承自父类的输入参数（如 search_query、ingest_data 等）
        *LCVectorStoreComponent.inputs,
        # 嵌入模型句柄输入，用于将文本转换为向量
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        # 返回的搜索结果数量
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            value=4,
            advanced=True,
        ),
    ]

    # 使用缓存装饰器，避免重复构建向量存储实例
    @check_cached_vector_store
    def build_vector_store(self) -> VectorStore:
        """Build and return a Pinecone vector store instance."""
        # 动态导入 langchain-pinecone 库，缺失时给出安装提示
        try:
            from langchain_pinecone import PineconeVectorStore
        except ImportError as e:
            msg = "langchain-pinecone is not installed. Please install it with `pip install langchain-pinecone`."
            raise ValueError(msg) from e

        try:
            # 导入距离策略枚举
            from langchain_pinecone._utilities import DistanceStrategy

            # 使用 Float32Embeddings 包装嵌入模型，确保输出为 float32 格式
            wrapped_embeddings = Float32Embeddings(self.embedding)

            # 将距离策略字符串转换为枚举值（如 "Cosine" -> DistanceStrategy.COSINE）
            distance_strategy = self.distance_strategy.replace(" ", "_").upper()
            distance_strategy = DistanceStrategy[distance_strategy]

            # 初始化 Pinecone 向量存储实例
            pinecone = PineconeVectorStore(
                index_name=self.index_name,
                embedding=wrapped_embeddings,  # 使用包装后的嵌入模型
                text_key=self.text_key,
                namespace=self.namespace,
                distance_strategy=distance_strategy,
                pinecone_api_key=self.pinecone_api_key,
            )
        except Exception as e:
            # 构建向量存储失败时抛出异常
            error_msg = "Error building Pinecone vector store"
            raise ValueError(error_msg) from e
        else:
            # 准备要导入的数据
            self.ingest_data = self._prepare_ingest_data()

            # 处理待导入的文档列表
            documents = []
            if self.ingest_data:
                # 将 Langflow 的 Data 对象转换为 LangChain Document 对象

                for doc in self.ingest_data:
                    if isinstance(doc, Data):
                        # Data 对象需要先转换为 LC Document 格式
                        documents.append(doc.to_lc_document())
                    else:
                        documents.append(doc)

                # 将文档批量添加到 Pinecone 向量存储
                if documents:
                    pinecone.add_documents(documents)

            return pinecone

    # 在向量存储中搜索文档，返回与查询最相似的结果
    def search_documents(self) -> list[Data]:
        """Search documents in the vector store."""
        try:
            # 校验搜索查询：必须是非空字符串
            if not self.search_query or not isinstance(self.search_query, str) or not self.search_query.strip():
                return []

            # 构建向量存储并执行相似度搜索
            vector_store = self.build_vector_store()
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
            )
        except Exception as e:
            # 搜索失败时抛出异常
            error_msg = "Error searching documents"
            raise ValueError(error_msg) from e
        else:
            # 将 LangChain Document 转换为 Langflow Data 对象
            data = docs_to_data(docs)
            # 更新组件状态，用于前端展示
            self.status = data
            return data


# 嵌入模型包装器，确保所有向量输出为 float32 格式（Pinecone 要求）
class Float32Embeddings:
    """Wrapper class to ensure float32 embeddings."""

    def __init__(self, base_embeddings):
        # 保存原始嵌入模型实例
        self.base_embeddings = base_embeddings

    # 批量为文档文本生成 float32 嵌入向量
    def embed_documents(self, texts):
        embeddings = self.base_embeddings.embed_documents(texts)
        if isinstance(embeddings, np.ndarray):
            return [[self._force_float32(x) for x in vec] for vec in embeddings]
        return [[self._force_float32(x) for x in vec] for vec in embeddings]

    # 为单条查询文本生成 float32 嵌入向量
    def embed_query(self, text):
        embedding = self.base_embeddings.embed_query(text)
        if isinstance(embedding, np.ndarray):
            return [self._force_float32(x) for x in embedding]
        return [self._force_float32(x) for x in embedding]

    def _force_float32(self, value):
        """Convert any numeric type to Python float."""
        # 将数值强制转换为 float32，再转为 Python float 以兼容 Pinecone
        return float(np.float32(value))
