# 标准库：UUID 解析
from uuid import UUID

# LangChain Cassandra 图向量存储集成
from langchain_community.graph_vectorstores import CassandraGraphVectorStore

# 向量存储组件基类、缓存检查装饰器、数据转换工具
from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.helpers.data import docs_to_data
from lfx.inputs.inputs import DictInput, FloatInput
from lfx.io import (
    DropdownInput,
    HandleInput,
    IntInput,
    MessageTextInput,
    SecretStrInput,
)
from lfx.schema.data import Data


# Cassandra 图向量存储组件，支持基于图结构的向量存储与遍历搜索
class CassandraGraphVectorStoreComponent(LCVectorStoreComponent):
    display_name = "Cassandra Graph"
    # 组件描述：Cassandra 图向量存储
    description = "Cassandra Graph Vector Store"
    name = "CassandraGraph"
    icon = "Cassandra"

    # 输入参数定义
    inputs = [
        # 数据库连接点或 Astra DB 数据库 ID
        MessageTextInput(
            name="database_ref",
            display_name="Contact Points / Astra Database ID",
            info="Contact points for the database (or Astra DB database ID)",
            required=True,
        ),
        # 数据库用户名（Astra DB 可留空）
        MessageTextInput(
            name="username", display_name="Username", info="Username for the database (leave empty for Astra DB)."
        ),
        # 数据库密码或 Astra DB Token
        SecretStrInput(
            name="token",
            display_name="Password / Astra DB Token",
            info="User password for the database (or Astra DB token).",
            required=True,
        ),
        # 键空间（Astra DB 命名空间）
        MessageTextInput(
            name="keyspace",
            display_name="Keyspace",
            info="Table Keyspace (or Astra DB namespace).",
            required=True,
        ),
        # 节点表名（Astra DB 集合名称）
        MessageTextInput(
            name="table_name",
            display_name="Table Name",
            info="The name of the table (or Astra DB collection) where vectors will be stored.",
            required=True,
        ),
        # 表初始化模式：同步/关闭
        DropdownInput(
            name="setup_mode",
            display_name="Setup Mode",
            info="Configuration mode for setting up the Cassandra table, with options like 'Sync' or 'Off'.",
            options=["Sync", "Off"],
            value="Sync",
            advanced=True,
        ),
        # Cassandra 集群额外参数
        DictInput(
            name="cluster_kwargs",
            display_name="Cluster arguments",
            info="Optional dictionary of additional keyword arguments for the Cassandra cluster.",
            advanced=True,
            list=True,
        ),
        *LCVectorStoreComponent.inputs,
        # 嵌入模型输入
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        # 返回结果数量
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            value=4,
            advanced=True,
        ),
        # 搜索类型选择：遍历/MMR遍历/相似度/带阈值相似度/MMR
        DropdownInput(
            name="search_type",
            display_name="Search Type",
            info="Search type to use",
            options=[
                "Traversal",
                "MMR traversal",
                "Similarity",
                "Similarity with score threshold",
                "MMR (Max Marginal Relevance)",
            ],
            value="Traversal",
            advanced=True,
        ),
        # 图遍历深度（用于遍历和 MMR 遍历搜索）
        IntInput(
            name="depth",
            display_name="Depth of traversal",
            info="The maximum depth of edges to traverse. (when using 'Traversal' or 'MMR traversal')",
            value=1,
            advanced=True,
        ),
        # 搜索分数阈值
        FloatInput(
            name="search_score_threshold",
            display_name="Search Score Threshold",
            info="Minimum similarity score threshold for search results. "
            "(when using 'Similarity with score threshold')",
            value=0,
            advanced=True,
        ),
        # 搜索元数据过滤器
        DictInput(
            name="search_filter",
            display_name="Search Metadata Filter",
            info="Optional dictionary of filters to apply to the search query.",
            advanced=True,
            list=True,
        ),
    ]

    # 构建 Cassandra 图向量存储实例（带缓存检查）
    @check_cached_vector_store
    def build_vector_store(self) -> CassandraGraphVectorStore:
        try:
            import cassio
            from langchain_community.utilities.cassandra import SetupMode
        except ImportError as e:
            msg = "Could not import cassio integration package. Please install it with `pip install cassio`."
            raise ImportError(msg) from e

        database_ref = self.database_ref

        try:
            UUID(self.database_ref)
            is_astra = True
        except ValueError:
            is_astra = False
            if "," in self.database_ref:
                # use a copy because we can't change the type of the parameter
                database_ref = self.database_ref.split(",")

        if is_astra:
            cassio.init(
                database_id=database_ref,
                token=self.token,
                cluster_kwargs=self.cluster_kwargs,
            )
        else:
            cassio.init(
                contact_points=database_ref,
                username=self.username,
                password=self.token,
                cluster_kwargs=self.cluster_kwargs,
            )

        self.ingest_data = self._prepare_ingest_data()

        documents = []

        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        setup_mode = SetupMode.OFF if self.setup_mode == "Off" else SetupMode.SYNC

        if documents:
            self.log(f"Adding {len(documents)} documents to the Vector Store.")
            store = CassandraGraphVectorStore.from_documents(
                documents=documents,
                embedding=self.embedding,
                node_table=self.table_name,
                keyspace=self.keyspace,
            )
        else:
            self.log("No documents to add to the Vector Store.")
            store = CassandraGraphVectorStore(
                embedding=self.embedding,
                node_table=self.table_name,
                keyspace=self.keyspace,
                setup_mode=setup_mode,
            )
        return store

    # 将用户选择的搜索类型映射为 LangChain 内部搜索类型字符串
    def _map_search_type(self) -> str:
        if self.search_type == "Similarity":
            return "similarity"
        if self.search_type == "Similarity with score threshold":
            return "similarity_score_threshold"
        if self.search_type == "MMR (Max Marginal Relevance)":
            return "mmr"
        if self.search_type == "MMR Traversal":
            return "mmr_traversal"
        return "traversal"

    # 搜索文档并返回结果
    def search_documents(self) -> list[Data]:
        vector_store = self.build_vector_store()

        self.log(f"Search input: {self.search_query}")
        self.log(f"Search type: {self.search_type}")
        self.log(f"Number of results: {self.number_of_results}")

        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            try:
                search_type = self._map_search_type()
                search_args = self._build_search_args()

                self.log(f"Search args: {search_args}")

                docs = vector_store.search(query=self.search_query, search_type=search_type, **search_args)
            except KeyError as e:
                if "content" in str(e):
                    msg = (
                        "You should ingest data through Langflow (or LangChain) to query it in Langflow. "
                        "Your collection does not contain a field name 'content'."
                    )
                    raise ValueError(msg) from e
                raise

            self.log(f"Retrieved documents: {len(docs)}")

            data = docs_to_data(docs)
            self.status = data
            return data
        return []

    # 构建搜索参数字典
    def _build_search_args(self):
        args = {
            "k": self.number_of_results,
            "score_threshold": self.search_score_threshold,
            "depth": self.depth,
        }

        if self.search_filter:
            clean_filter = {k: v for k, v in self.search_filter.items() if k and v}
            if len(clean_filter) > 0:
                args["filter"] = clean_filter
        return args

    # 获取检索器参数，供 LangChain 检索器使用
    def get_retriever_kwargs(self):
        search_args = self._build_search_args()
        return {
            "search_type": self._map_search_type(),
            "search_kwargs": search_args,
        }
