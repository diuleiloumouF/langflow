# Weaviate 向量存储组件，提供 Weaviate 向量数据库的文档存储和相似度搜索功能
import weaviate
from langchain_weaviate import WeaviateVectorStore

from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.helpers.data import docs_to_data
from lfx.io import BoolInput, HandleInput, IntInput, SecretStrInput, StrInput
from lfx.schema.data import Data


# Weaviate 向量存储组件，支持文档索引和相似度搜索
class WeaviateVectorStoreComponent(LCVectorStoreComponent):
    # 组件显示名称
    display_name = "Weaviate"
    # 组件描述
    description = "Weaviate Vector Store with search capabilities"
    # 组件内部名称
    name = "Weaviate"
    # 组件图标
    icon = "Weaviate"

    # 组件输入参数定义
    inputs = [
        # Weaviate 服务地址
        StrInput(name="url", display_name="Weaviate URL", value="http://localhost:8080", required=True),
        # API 密钥（可选，用于认证）
        SecretStrInput(name="api_key", display_name="API Key", required=False),
        # 索引名称（需要首字母大写）
        StrInput(
            name="index_name",
            display_name="Index Name",
            required=True,
            info="Requires capitalized index name.",
        ),
        # 文档文本字段的键名
        StrInput(name="text_key", display_name="Text Key", value="text", advanced=True),
        *LCVectorStoreComponent.inputs,
        # 嵌入模型输入
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        # 返回的搜索结果数量
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            value=4,
            advanced=True,
        ),
        # 是否按文本内容搜索（而非向量相似度）
        BoolInput(name="search_by_text", display_name="Search By Text", advanced=True),
    ]

    # 构建 Weaviate 向量存储实例
    @check_cached_vector_store
    def build_vector_store(self) -> WeaviateVectorStore:
        # 根据是否提供 API 密钥创建不同认证方式的客户端
        if self.api_key:
            auth_config = weaviate.AuthApiKey(api_key=self.api_key)
            client = weaviate.Client(url=self.url, auth_client_secret=auth_config)
        else:
            client = weaviate.Client(url=self.url)

        # Weaviate 要求索引名称首字母大写
        if self.index_name != self.index_name.capitalize():
            msg = f"Weaviate requires the index name to be capitalized. Use: {self.index_name.capitalize()}"
            raise ValueError(msg)

        # Convert DataFrame to Data if needed using parent's method
        # 准备要导入的数据
        self.ingest_data = self._prepare_ingest_data()

        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        # 如果有文档和嵌入模型，则通过文档直接创建向量存储
        if documents and self.embedding:
            return WeaviateVectorStore.from_documents(
                client=client,
                index_name=self.index_name,
                documents=documents,
                embedding=self.embedding,
                by_text=self.search_by_text,
            )

        # 否则创建空的向量存储连接
        return WeaviateVectorStore(
            client=client,
            index_name=self.index_name,
            text_key=self.text_key,
            embedding=self.embedding,
            by_text=self.search_by_text,
        )

    # 搜索文档：在 Weaviate 向量存储中执行相似度搜索
    def search_documents(self) -> list[Data]:
        vector_store = self.build_vector_store()

        # 仅在搜索查询非空时执行搜索
        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
            )

            data = docs_to_data(docs)
            self.status = data
            return data
        return []
