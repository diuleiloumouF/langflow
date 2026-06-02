from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import Client, create_client

from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.helpers.data import docs_to_data
from lfx.io import HandleInput, IntInput, SecretStrInput, StrInput
from lfx.schema.data import Data


class SupabaseVectorStoreComponent(LCVectorStoreComponent):
    """Supabase 向量存储组件，用于将文档存储到 Supabase 并提供相似性搜索功能。"""

    # 组件显示名称，用于在画布上展示
    display_name = "Supabase"
    # 组件描述信息
    description = "Supabase Vector Store with search capabilities"
    # 组件内部名称，用于标识组件类型
    name = "SupabaseVectorStore"
    # 组件图标
    icon = "Supabase"

    # 组件输入参数定义
    inputs = [
        # Supabase 数据库的 URL 地址
        StrInput(name="supabase_url", display_name="Supabase URL", required=True),
        # Supabase 服务密钥，用于身份验证
        SecretStrInput(name="supabase_service_key", display_name="Supabase Service Key", required=True),
        # 存储向量的表名，高级配置项
        StrInput(name="table_name", display_name="Table Name", advanced=True),
        # Supabase RPC 查询函数名称
        StrInput(name="query_name", display_name="Query Name"),
        # 继承父类的输入参数（如记录管理、搜索查询等）
        *LCVectorStoreComponent.inputs,
        # 嵌入模型输入，用于将文本转换为向量
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        # 搜索结果返回数量，默认为 4
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            value=4,
            advanced=True,
        ),
    ]

    @check_cached_vector_store
    def build_vector_store(self) -> SupabaseVectorStore:
        """构建 Supabase 向量存储实例。

        如果有文档数据则写入 Supabase，否则仅创建向量存储连接。
        """
        # 创建 Supabase 客户端连接
        supabase: Client = create_client(self.supabase_url, supabase_key=self.supabase_service_key)

        # Convert DataFrame to Data if needed using parent's method
        # 将输入数据统一转换为可处理的格式
        self.ingest_data = self._prepare_ingest_data()

        # 将所有输入数据转换为 LangChain 文档格式
        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                # 如果是 Data 类型，调用 to_lc_document() 转换
                documents.append(_input.to_lc_document())
            else:
                # 已经是 LangChain Document 类型，直接添加
                documents.append(_input)

        # 根据是否有文档决定构建方式
        if documents:
            # 有文档时，通过 from_documents 将文档写入 Supabase 并创建向量存储
            supabase_vs = SupabaseVectorStore.from_documents(
                documents=documents,
                embedding=self.embedding,
                query_name=self.query_name,
                client=supabase,
                table_name=self.table_name,
            )
        else:
            # 无文档时，仅建立与已有向量存储的连接
            supabase_vs = SupabaseVectorStore(
                client=supabase,
                embedding=self.embedding,
                table_name=self.table_name,
                query_name=self.query_name,
            )

        return supabase_vs

    def search_documents(self) -> list[Data]:
        """在 Supabase 向量存储中执行相似性搜索，返回最相关的文档。"""
        # 获取向量存储实例
        vector_store = self.build_vector_store()

        # 检查搜索查询是否有效
        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            # 执行相似性搜索，返回最相近的 k 个结果
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
            )

            # 将 LangChain Document 列表转换为 Data 列表
            data = docs_to_data(docs)
            # 将搜索结果保存到状态中，供后续组件使用
            self.status = data
            return data
        # 没有有效的搜索查询时返回空列表
        return []
