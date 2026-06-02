from datetime import timedelta

from langchain_community.vectorstores import CouchbaseVectorStore

from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.helpers.data import docs_to_data
from lfx.io import HandleInput, IntInput, SecretStrInput, StrInput
from lfx.schema.data import Data


class CouchbaseVectorStoreComponent(LCVectorStoreComponent):
    """Couchbase 向量存储组件，支持向量化存储和相似性搜索"""

    display_name = "Couchbase"
    description = "Couchbase Vector Store with search capabilities"
    name = "Couchbase"
    icon = "Couchbase"

    # 组件输入参数定义：连接信息、Bucket/Scope/Collection、索引、嵌入模型、返回结果数
    inputs = [
        SecretStrInput(
            name="couchbase_connection_string", display_name="Couchbase Cluster connection string", required=True
        ),
        StrInput(name="couchbase_username", display_name="Couchbase username", required=True),
        SecretStrInput(name="couchbase_password", display_name="Couchbase password", required=True),
        StrInput(name="bucket_name", display_name="Bucket Name", required=True),
        StrInput(name="scope_name", display_name="Scope Name", required=True),
        StrInput(name="collection_name", display_name="Collection Name", required=True),
        StrInput(name="index_name", display_name="Index Name", required=True),
        *LCVectorStoreComponent.inputs,
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            value=4,
            advanced=True,
        ),
    ]

    @check_cached_vector_store
    def build_vector_store(self) -> CouchbaseVectorStore:
        """构建 Couchbase 向量存储实例，连接集群并导入文档数据"""
        # 延迟导入 Couchbase SDK，避免未安装时影响其他组件
        try:
            from couchbase.auth import PasswordAuthenticator
            from couchbase.cluster import Cluster
            from couchbase.options import ClusterOptions
        except ImportError as e:
            msg = "Failed to import Couchbase dependencies. Install it using `uv pip install langflow[couchbase] --pre`"
            raise ImportError(msg) from e

        # 使用用户名密码认证连接 Couchbase 集群，等待就绪（超时5秒）
        try:
            auth = PasswordAuthenticator(self.couchbase_username, self.couchbase_password)
            options = ClusterOptions(auth)
            cluster = Cluster(self.couchbase_connection_string, options)

            cluster.wait_until_ready(timedelta(seconds=5))
        except Exception as e:
            msg = f"Failed to connect to Couchbase: {e}"
            raise ValueError(msg) from e

        # 准备待导入的数据
        self.ingest_data = self._prepare_ingest_data()

        # 将 Data 对象转换为 LangChain Document 格式
        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        # 如果有文档数据，使用 from_documents 创建向量存储（自动向量化并存储）
        # 否则仅创建空的向量存储连接
        if documents:
            couchbase_vs = CouchbaseVectorStore.from_documents(
                documents=documents,
                cluster=cluster,
                bucket_name=self.bucket_name,
                scope_name=self.scope_name,
                collection_name=self.collection_name,
                embedding=self.embedding,
                index_name=self.index_name,
            )

        else:
            couchbase_vs = CouchbaseVectorStore(
                cluster=cluster,
                bucket_name=self.bucket_name,
                scope_name=self.scope_name,
                collection_name=self.collection_name,
                embedding=self.embedding,
                index_name=self.index_name,
            )

        return couchbase_vs

    def search_documents(self) -> list[Data]:
        """根据搜索查询在向量存储中执行相似性搜索，返回最相关的文档"""
        vector_store = self.build_vector_store()

        # 仅在搜索查询非空时执行相似性搜索
        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
            )

            # 将 LangChain Document 转换为 Data 格式并设置状态输出
            data = docs_to_data(docs)
            self.status = data
            return data
        return []
