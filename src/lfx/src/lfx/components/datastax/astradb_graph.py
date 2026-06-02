# 高性能 JSON 序列化库
import orjson

# AstraDB 基础组件、向量存储组件基类、数据转换工具
from lfx.base.datastax.astradb_base import AstraDBBaseComponent
from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.helpers.data import docs_to_data
from lfx.inputs.inputs import (
    DictInput,
    DropdownInput,
    FloatInput,
    IntInput,
    StrInput,
)
from lfx.schema.data import Data


# Astra DB 图向量存储组件，基于 Astra DB 实现图向量存储（已弃用，推荐使用 GraphRAG）
class AstraDBGraphVectorStoreComponent(AstraDBBaseComponent, LCVectorStoreComponent):
    display_name: str = "Astra DB Graph"
    # 组件描述：使用 Astra DB 实现图向量存储
    description: str = "Implementation of Graph Vector Store using Astra DB"
    name = "AstraDBGraph"
    documentation: str = "https://docs.langflow.org/bundles-datastax"
    icon: str = "AstraDB"
    # 标记为已弃用组件
    legacy: bool = True
    replacement = ["datastax.GraphRAG"]

    inputs = [
        *AstraDBBaseComponent.inputs,
        *LCVectorStoreComponent.inputs,
        StrInput(
            name="metadata_incoming_links_key",
            display_name="Metadata incoming links key",
            info="Metadata key used for incoming links.",
            advanced=True,
        ),
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            advanced=True,
            value=4,
        ),
        DropdownInput(
            name="search_type",
            display_name="Search Type",
            info="Search type to use",
            options=[
                "Similarity",
                "Similarity with score threshold",
                "MMR (Max Marginal Relevance)",
                "Graph Traversal",
                "MMR (Max Marginal Relevance) Graph Traversal",
            ],
            value="MMR (Max Marginal Relevance) Graph Traversal",
            advanced=True,
        ),
        FloatInput(
            name="search_score_threshold",
            display_name="Search Score Threshold",
            info="Minimum similarity score threshold for search results. "
            "(when using 'Similarity with score threshold')",
            value=0,
            advanced=True,
        ),
        DictInput(
            name="search_filter",
            display_name="Search Metadata Filter",
            info="Optional dictionary of filters to apply to the search query.",
            advanced=True,
            is_list=True,
        ),
    ]

    # 构建 Astra DB 图向量存储实例（带缓存检查）
    @check_cached_vector_store
    def build_vector_store(self):
        try:
            from langchain_astradb import AstraDBGraphVectorStore
            from langchain_astradb.utils.astradb import SetupMode
        except ImportError as e:
            msg = (
                "Could not import langchain Astra DB integration package. "
                "Please install it with `pip install langchain-astradb`."
            )
            raise ImportError(msg) from e

        try:
            if not self.setup_mode:
                self.setup_mode = self._inputs["setup_mode"].options[0]

            setup_mode_value = SetupMode[self.setup_mode.upper()]
        except KeyError as e:
            msg = f"Invalid setup mode: {self.setup_mode}"
            raise ValueError(msg) from e

        try:
            self.log(f"Initializing Graph Vector Store {self.collection_name}")

            vector_store = AstraDBGraphVectorStore(
                embedding=self.embedding_model,
                collection_name=self.collection_name,
                metadata_incoming_links_key=self.metadata_incoming_links_key or "incoming_links",
                token=self.token,
                api_endpoint=self.get_api_endpoint(),
                namespace=self.get_keyspace(),
                environment=self.environment,
                metric=self.metric or None,
                batch_size=self.batch_size or None,
                bulk_insert_batch_concurrency=self.bulk_insert_batch_concurrency or None,
                bulk_insert_overwrite_concurrency=self.bulk_insert_overwrite_concurrency or None,
                bulk_delete_concurrency=self.bulk_delete_concurrency or None,
                setup_mode=setup_mode_value,
                pre_delete_collection=self.pre_delete_collection,
                metadata_indexing_include=[s for s in self.metadata_indexing_include if s] or None,
                metadata_indexing_exclude=[s for s in self.metadata_indexing_exclude if s] or None,
                collection_indexing_policy=orjson.loads(self.collection_indexing_policy.encode("utf-8"))
                if self.collection_indexing_policy
                else None,
            )
        except Exception as e:
            msg = f"Error initializing AstraDBGraphVectorStore: {e}"
            raise ValueError(msg) from e

        self.log(f"Vector Store initialized: {vector_store.astra_env.collection_name}")
        self._add_documents_to_vector_store(vector_store)

        return vector_store

    # 向向量存储中添加文档
    def _add_documents_to_vector_store(self, vector_store) -> None:
        self.ingest_data = self._prepare_ingest_data()

        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                msg = "Vector Store Inputs must be Data objects."
                raise TypeError(msg)

        if documents:
            self.log(f"Adding {len(documents)} documents to the Vector Store.")
            try:
                vector_store.add_documents(documents)
            except Exception as e:
                msg = f"Error adding documents to AstraDBGraphVectorStore: {e}"
                raise ValueError(msg) from e
        else:
            self.log("No documents to add to the Vector Store.")

    # 将用户选择的搜索类型映射为 LangChain 内部搜索类型字符串
    def _map_search_type(self) -> str:
        match self.search_type:
            case "Similarity":
                return "similarity"
            case "Similarity with score threshold":
                return "similarity_score_threshold"
            case "MMR (Max Marginal Relevance)":
                return "mmr"
            case "Graph Traversal":
                return "traversal"
            case "MMR (Max Marginal Relevance) Graph Traversal":
                return "mmr_traversal"
            case _:
                return "similarity"

    # 构建搜索参数字典
    def _build_search_args(self):
        args = {
            "k": self.number_of_results,
            "score_threshold": self.search_score_threshold,
        }

        if self.search_filter:
            clean_filter = {k: v for k, v in self.search_filter.items() if k and v}
            if len(clean_filter) > 0:
                args["filter"] = clean_filter
        return args

    # 搜索文档并返回结果
    def search_documents(self, vector_store=None) -> list[Data]:
        if not vector_store:
            vector_store = self.build_vector_store()

        self.log("Searching for documents in AstraDBGraphVectorStore.")
        self.log(f"Search query: {self.search_query}")
        self.log(f"Search type: {self.search_type}")
        self.log(f"Number of results: {self.number_of_results}")

        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            try:
                search_type = self._map_search_type()
                search_args = self._build_search_args()

                docs = vector_store.search(query=self.search_query, search_type=search_type, **search_args)

                # Drop links from the metadata. At this point the links don't add any value for building the
                # context and haven't been restored to json which causes the conversion to fail.
                self.log("Removing links from metadata.")
                for doc in docs:
                    if "links" in doc.metadata:
                        doc.metadata.pop("links")

            except Exception as e:
                msg = f"Error performing search in AstraDBGraphVectorStore: {e}"
                raise ValueError(msg) from e

            self.log(f"Retrieved documents: {len(docs)}")

            data = docs_to_data(docs)

            self.log(f"Converted documents to data: {len(data)}")

            self.status = data
            return data
        self.log("No search input provided. Skipping search.")
        return []

    # 获取检索器参数，供 LangChain 检索器使用
    def get_retriever_kwargs(self):
        search_args = self._build_search_args()
        return {
            "search_type": self._map_search_type(),
            "search_kwargs": search_args,
        }
