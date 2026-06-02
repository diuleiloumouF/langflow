# Milvus 向量存储组件
# 该模块提供 Milvus 向量数据库的集成，支持向量存储和相似度搜索功能
from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.helpers.data import docs_to_data
from lfx.io import (
    BoolInput,
    DictInput,
    DropdownInput,
    FloatInput,
    HandleInput,
    IntInput,
    SecretStrInput,
    StrInput,
)
from lfx.schema.data import Data


class MilvusVectorStoreComponent(LCVectorStoreComponent):
    """Milvus vector store with search capabilities."""

    # 组件在界面上显示的名称
    display_name: str = "Milvus"
    # 组件的描述信息
    description: str = "Milvus vector store with search capabilities"
    # 组件内部标识名称
    name = "Milvus"
    # 组件图标
    icon = "Milvus"

    # 组件输入参数定义
    inputs = [
        # 集合名称，用于在 Milvus 中标识向量集合
        StrInput(name="collection_name", display_name="Collection Name", value="langflow"),
        # 集合描述，对集合进行简要说明
        StrInput(name="collection_description", display_name="Collection Description", value=""),
        # Milvus 服务连接地址，默认为本地地址
        StrInput(
            name="uri",
            display_name="Connection URI",
            value="http://localhost:19530",
        ),
        # 连接令牌/密码，如果不需要认证可留空
        SecretStrInput(
            name="password",
            display_name="Milvus Token",
            value="",
            info="Ignore this field if no token is required to make connection.",
        ),
        # 其他连接参数，以字典形式传入高级连接配置
        DictInput(name="connection_args", display_name="Other Connection Arguments", advanced=True),
        # 主键字段名称，Milvus 集合中的主键列
        StrInput(name="primary_field", display_name="Primary Field Name", value="pk"),
        # 文本字段名称，存储原始文本内容的列
        StrInput(name="text_field", display_name="Text Field Name", value="text"),
        # 向量字段名称，存储向量嵌入的列
        StrInput(name="vector_field", display_name="Vector Field Name", value="vector"),
        # 数据一致性级别，控制查询时的数据一致性保证
        DropdownInput(
            name="consistency_level",
            display_name="Consistencey Level",
            options=["Bounded", "Session", "Strong", "Eventual"],
            value="Session",
            advanced=True,
        ),
        # 索引参数，用于配置向量索引的构建方式
        DictInput(name="index_params", display_name="Index Parameters", advanced=True),
        # 搜索参数，用于配置相似度搜索的行为
        DictInput(name="search_params", display_name="Search Parameters", advanced=True),
        # 是否删除旧集合，开启后会先删除同名集合再重新创建
        BoolInput(name="drop_old", display_name="Drop Old Collection", value=False, advanced=True),
        # 连接超时时间（秒）
        FloatInput(name="timeout", display_name="Timeout", advanced=True),
        # 继承父类的输入参数（搜索查询、数据输入等）
        *LCVectorStoreComponent.inputs,
        # 嵌入模型，用于将文本转换为向量表示
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        # 返回的相似结果数量
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            value=4,
            advanced=True,
        ),
    ]

    @check_cached_vector_store
    def build_vector_store(self):
        """构建 Milvus 向量存储实例，将输入数据写入 Milvus 数据库"""
        try:
            # 延迟导入 langchain-milvus 集成包
            from langchain_milvus.vectorstores import Milvus as LangchainMilvus
        except ImportError as e:
            msg = "Could not import Milvus integration package. Please install it with `pip install langchain-milvus`."
            raise ImportError(msg) from e
        # 将 URI 和令牌合并到连接参数中
        self.connection_args.update(uri=self.uri, token=self.password)
        # 创建 Milvus 向量存储实例，配置集合、索引、搜索等参数
        milvus_store = LangchainMilvus(
            embedding_function=self.embedding,
            collection_name=self.collection_name,
            collection_description=self.collection_description,
            connection_args=self.connection_args,
            consistency_level=self.consistency_level,
            index_params=self.index_params,
            search_params=self.search_params,
            drop_old=self.drop_old,
            auto_id=True,
            primary_field=self.primary_field,
            text_field=self.text_field,
            vector_field=self.vector_field,
            timeout=self.timeout,
        )

        # Convert DataFrame to Data if needed using parent's method
        # 使用父类方法将 DataFrame 格式的输入数据转换为 Data 对象
        self.ingest_data = self._prepare_ingest_data()

        # 将输入数据转换为 LangChain Document 格式
        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                # Data 类型转为 LangChain Document
                documents.append(_input.to_lc_document())
            else:
                # 已经是 Document 类型，直接使用
                documents.append(_input)

        # 如果有文档数据，则批量写入 Milvus
        if documents:
            milvus_store.add_documents(documents)

        return milvus_store

    def search_documents(self) -> list[Data]:
        """在 Milvus 中执行相似度搜索，返回与查询最相关的文档"""
        vector_store = self.build_vector_store()

        # 仅在搜索查询非空时执行搜索
        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            # 执行相似度搜索，返回 k 个最相似的结果
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
            )

            # 将 LangChain Document 转换为 Langflow Data 格式
            data = docs_to_data(docs)
            # 将搜索结果保存到组件状态，供前端展示
            self.status = data
            return data
        # 无搜索查询时返回空列表
        return []
