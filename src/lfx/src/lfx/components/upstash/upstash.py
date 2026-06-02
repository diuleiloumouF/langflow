from langchain_community.vectorstores import UpstashVectorStore

from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.helpers.data import docs_to_data
from lfx.io import (
    HandleInput,
    IntInput,
    MultilineInput,
    SecretStrInput,
    StrInput,
)
from lfx.schema.data import Data


# Upstash 向量存储组件，提供基于 Upstash 的向量搜索和存储功能
class UpstashVectorStoreComponent(LCVectorStoreComponent):
    # 组件显示名称
    display_name = "Upstash"
    # 组件描述信息
    description = "Upstash Vector Store with search capabilities"
    # 组件内部名称
    name = "Upstash"
    # 组件图标
    icon = "Upstash"

    # 组件输入参数定义
    inputs = [
        StrInput(
            name="index_url",
            display_name="Index URL",
            info="The URL of the Upstash index.",
            required=True,
        ),
        SecretStrInput(
            name="index_token",
            display_name="Upstash Index Token",
            info="The token for the Upstash index.",
            required=True,
        ),
        StrInput(
            name="text_key",
            display_name="Text Key",
            info="The key in the record to use as text.",
            value="text",
            advanced=True,
        ),
        StrInput(
            name="namespace",
            display_name="Namespace",
            info="Leave empty for default namespace.",
        ),
        *LCVectorStoreComponent.inputs,
        MultilineInput(
            name="metadata_filter",
            display_name="Metadata Filter",
            info="Filters documents by metadata. Look at the documentation for more information.",
        ),
        HandleInput(
            name="embedding",
            display_name="Embedding",
            input_types=["Embeddings"],
            info="To use Upstash's embeddings, don't provide an embedding.",
        ),
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            value=4,
            advanced=True,
        ),
    ]

    # 构建 Upstash 向量存储实例
    @check_cached_vector_store
    def build_vector_store(self) -> UpstashVectorStore:
        use_upstash_embedding = self.embedding is None

        # Convert DataFrame to Data if needed using parent's method
        self.ingest_data = self._prepare_ingest_data()

        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        if documents:
            if use_upstash_embedding:
                upstash_vs = UpstashVectorStore(
                    embedding=use_upstash_embedding,
                    text_key=self.text_key,
                    index_url=self.index_url,
                    index_token=self.index_token,
                    namespace=self.namespace,
                )
                upstash_vs.add_documents(documents)
            else:
                upstash_vs = UpstashVectorStore.from_documents(
                    documents=documents,
                    embedding=self.embedding,
                    text_key=self.text_key,
                    index_url=self.index_url,
                    index_token=self.index_token,
                    namespace=self.namespace,
                )
        else:
            upstash_vs = UpstashVectorStore(
                embedding=self.embedding or use_upstash_embedding,
                text_key=self.text_key,
                index_url=self.index_url,
                index_token=self.index_token,
                namespace=self.namespace,
            )

        return upstash_vs

    # 搜索文档，使用相似度搜索在 Upstash 向量存储中查找相关文档
    def search_documents(self) -> list[Data]:
        vector_store = self.build_vector_store()

        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
                filter=self.metadata_filter,
            )

            data = docs_to_data(docs)
            self.status = data
            return data
        return []
