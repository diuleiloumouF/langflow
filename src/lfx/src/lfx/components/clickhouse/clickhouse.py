# ClickHouse 向量存储的 LangChain 集成
from langchain_community.vectorstores import Clickhouse, ClickhouseSettings

# 向量存储组件基类、缓存检查装饰器
from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store

# 文档转数据工具函数
from lfx.helpers.data import docs_to_data

# 输入组件类型
from lfx.inputs.inputs import BoolInput, FloatInput
from lfx.io import (
    DictInput,
    DropdownInput,
    HandleInput,
    IntInput,
    SecretStrInput,
    StrInput,
)

# 数据模型
from lfx.schema.data import Data


# ClickHouse 向量存储组件，支持向量搜索和相似度检索
class ClickhouseVectorStoreComponent(LCVectorStoreComponent):
    """ClickHouse 向量存储组件，提供搜索功能。"""

    display_name = "ClickHouse"
    description = "ClickHouse Vector Store with search capabilities"
    name = "Clickhouse"
    icon = "Clickhouse"

    # 输入参数定义
    inputs = [
        # 服务器主机名
        StrInput(name="host", display_name="hostname", required=True, value="localhost"),
        # 服务端口
        IntInput(name="port", display_name="port", required=True, value=8123),
        # 数据库名称
        StrInput(name="database", display_name="database", required=True),
        # 数据表名称
        StrInput(name="table", display_name="Table name", required=True),
        # ClickHouse 用户名
        StrInput(name="username", display_name="The ClickHouse user name.", required=True),
        # ClickHouse 密码
        SecretStrInput(name="password", display_name="Clickhouse Password", required=True),
        # 索引类型：annoy 或 vector_similarity
        DropdownInput(
            name="index_type",
            display_name="index_type",
            options=["annoy", "vector_similarity"],
            info="Type of the index.",
            value="annoy",
            advanced=True,
        ),
        # 距离度量方式
        DropdownInput(
            name="metric",
            display_name="metric",
            options=["angular", "euclidean", "manhattan", "hamming", "dot"],
            info="Metric to compute distance.",
            value="angular",
            advanced=True,
        ),
        # 是否使用 HTTPS/TLS 加密连接
        BoolInput(
            name="secure",
            display_name="Use https/TLS. This overrides inferred values from the interface or port arguments.",
            value=False,
            advanced=True,
        ),
        # 索引参数
        StrInput(name="index_param", display_name="Param of the index", value="100,'L2Distance'", advanced=True),
        # 索引查询参数
        DictInput(name="index_query_params", display_name="index query params", advanced=True),
        # 继承父类的输入参数
        *LCVectorStoreComponent.inputs,
        # 嵌入模型
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        # 返回结果数量
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            value=4,
            advanced=True,
        ),
        # 相似度分数阈值
        FloatInput(name="score_threshold", display_name="Score threshold", advanced=True),
    ]

    # 构建 ClickHouse 向量存储实例
    @check_cached_vector_store
    def build_vector_store(self) -> Clickhouse:
        try:
            import clickhouse_connect
        except ImportError as e:
            msg = (
                "Failed to import ClickHouse dependencies. "
                "Install it using `uv pip install langflow[clickhouse-connect] --pre`"
            )
            raise ImportError(msg) from e

        # 尝试连接 ClickHouse 并验证连接是否成功
        try:
            client = clickhouse_connect.get_client(
                host=self.host, port=self.port, username=self.username, password=self.password
            )
            client.command("SELECT 1")
        except Exception as e:
            msg = f"Failed to connect to Clickhouse: {e}"
            raise ValueError(msg) from e

        # 使用父类方法将 DataFrame 转换为 Data
        self.ingest_data = self._prepare_ingest_data()

        # 将输入数据转换为 LangChain Document 格式
        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        # 构建额外的索引参数
        kwargs = {}
        if self.index_param:
            kwargs["index_param"] = self.index_param.split(",")
        if self.index_query_params:
            kwargs["index_query_params"] = self.index_query_params

        # 配置 ClickHouse 向量存储设置
        settings = ClickhouseSettings(
            table=self.table,
            database=self.database,
            host=self.host,
            index_type=self.index_type,
            metric=self.metric,
            password=self.password,
            port=self.port,
            secure=self.secure,
            username=self.username,
            **kwargs,
        )
        # 根据是否有文档选择不同的初始化方式
        if documents:
            clickhouse_vs = Clickhouse.from_documents(documents=documents, embedding=self.embedding, config=settings)

        else:
            clickhouse_vs = Clickhouse(embedding=self.embedding, config=settings)

        return clickhouse_vs

    # 搜索文档：执行相似度检索并返回数据
    def search_documents(self) -> list[Data]:
        vector_store = self.build_vector_store()

        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            kwargs = {}
            if self.score_threshold:
                kwargs["score_threshold"] = self.score_threshold

            # 执行相似度搜索
            docs = vector_store.similarity_search(query=self.search_query, k=self.number_of_results, **kwargs)

            # 将搜索结果转换为 Data 格式
            data = docs_to_data(docs)
            self.status = data
            return data
        return []
