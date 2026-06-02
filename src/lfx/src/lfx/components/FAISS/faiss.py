from pathlib import Path

from langchain_community.vectorstores import FAISS

from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.helpers.data import docs_to_data
from lfx.io import BoolInput, HandleInput, IntInput, StrInput
from lfx.schema.data import Data


class FaissVectorStoreComponent(LCVectorStoreComponent):
    """FAISS 向量存储组件，提供搜索功能。"""

    # FAISS 向量存储组件，基于 LangChain 的 FAISS 实现，支持文档的向量索引和相似度搜索

    """FAISS Vector Store with search capabilities."""

    display_name: str = "FAISS"
    # 组件显示名称
    description: str = "FAISS Vector Store with search capabilities"
    # 组件描述信息
    name = "FAISS"
    # 组件内部名称标识
    icon = "FAISS"
    # 组件图标

    inputs = [
        # 索引名称输入参数，用于标识 FAISS 索引
        StrInput(
            name="index_name",
            display_name="Index Name",
            value="langflow_index",
        ),
        # 持久化目录输入参数，指定 FAISS 索引的保存路径
        StrInput(
            name="persist_directory",
            display_name="Persist Directory",
            info="Path to save the FAISS index. It will be relative to where Langflow is running.",
        ),
        # 继承父类的输入参数（包括搜索查询、数据源等）
        *LCVectorStoreComponent.inputs,
        # 允许危险反序列化开关，用于加载 pickle 文件时的安全控制
        BoolInput(
            name="allow_dangerous_deserialization",
            display_name="Allow Dangerous Deserialization",
            info="Set to True to allow loading pickle files. WARNING: Only enable this if you trust the source "
            "of the data. Malicious pickle files can execute arbitrary code on your system.",
            advanced=True,
            value=False,
        ),
        # 嵌入模型输入参数，用于将文本转换为向量
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        # 返回结果数量参数
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            advanced=True,
            value=4,
        ),
    ]

    @staticmethod
    def resolve_path(path: str) -> str:
        """Resolve the path relative to the Langflow root.

        Args:
            path: The path to resolve
        Returns:
            str: The resolved path as a string
        """
        # 解析相对于 Langflow 根目录的路径，返回绝对路径字符串
        return str(Path(path).resolve())

    def get_persist_directory(self) -> Path:
        """Returns the resolved persist directory path or the current directory if not set."""
        # 返回已解析的持久化目录路径，如果未设置则返回当前目录
        if self.persist_directory:
            return Path(self.resolve_path(self.persist_directory))
        return Path()

    @check_cached_vector_store
    def build_vector_store(self) -> FAISS:
        """Builds the FAISS object."""
        # 构建 FAISS 向量存储对象
        path = self.get_persist_directory()
        # 确保持久化目录存在
        path.mkdir(parents=True, exist_ok=True)

        # Convert DataFrame to Data if needed using parent's method
        # 如果需要，使用父类方法将 DataFrame 转换为 Data 对象
        self.ingest_data = self._prepare_ingest_data()

        # 将输入数据转换为 LangChain Document 格式
        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                # 如果是 Data 类型，转换为 LC Document
                documents.append(_input.to_lc_document())
            else:
                # 否则直接添加（已经是 Document 格式）
                documents.append(_input)

        # 使用文档列表和嵌入模型创建 FAISS 向量存储
        faiss = FAISS.from_documents(documents=documents, embedding=self.embedding)
        # 将向量存储保存到本地磁盘
        faiss.save_local(str(path), self.index_name)
        return faiss

    def search_documents(self) -> list[Data]:
        """Search for documents in the FAISS vector store."""
        # 在 FAISS 向量存储中搜索文档
        path = self.get_persist_directory()
        index_path = path / f"{self.index_name}.faiss"

        if not index_path.exists():
            # 索引文件不存在，构建新的向量存储
            vector_store = self.build_vector_store()
        else:
            # 从磁盘加载已有的 FAISS 索引
            vector_store = FAISS.load_local(
                folder_path=str(path),
                embeddings=self.embedding,
                index_name=self.index_name,
                allow_dangerous_deserialization=self.allow_dangerous_deserialization,
            )

        if not vector_store:
            msg = "Failed to load the FAISS index."
            raise ValueError(msg)

        # 如果有搜索查询，执行相似度搜索
        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
            )
            # 将搜索结果转换为 Data 格式返回
            return docs_to_data(docs)
        # 没有搜索查询时返回空列表
        return []
