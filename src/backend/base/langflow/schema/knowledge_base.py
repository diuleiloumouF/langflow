# 知识库相关的 Schema 定义
# 包含知识库信息、批量删除请求、列配置、分块信息等数据模型
from pydantic import BaseModel


# 知识库信息模型：描述知识库的元数据和状态
class KnowledgeBaseInfo(BaseModel):
    id: str
    dir_name: str = ""
    name: str
    embedding_provider: str | None = "Unknown"
    embedding_model: str | None = "Unknown"
    size: int = 0
    words: int = 0
    characters: int = 0
    chunks: int = 0
    avg_chunk_size: float = 0.0
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    separator: str | None = None
    status: str = "empty"
    failure_reason: str | None = None
    last_job_id: str | None = None
    source_types: list[str] = []
    column_config: list[dict] | None = None


# 批量删除知识库请求模型
class BulkDeleteRequest(BaseModel):
    kb_names: list[str]


# 列配置项模型：用于定义知识库中每列的向量化和标识属性
class ColumnConfigItem(BaseModel):
    column_name: str
    vectorize: bool = False
    identifier: bool = False


# 创建知识库请求模型
class CreateKnowledgeBaseRequest(BaseModel):
    name: str
    embedding_provider: str
    embedding_model: str
    column_config: list[ColumnConfigItem] | None = None


# 添加数据源请求模型
class AddSourceRequest(BaseModel):
    source_name: str
    files: list[str]  # List of file paths or file IDs


# 分块信息模型：描述知识库中的单个文本分块
class ChunkInfo(BaseModel):
    id: str
    content: str
    char_count: int
    metadata: dict | None = None


# 分页分块响应模型：返回分块列表及分页元数据
class PaginatedChunkResponse(BaseModel):
    chunks: list[ChunkInfo]
    total: int
    page: int
    limit: int
    total_pages: int
