# UUID 类型，用于生成唯一标识符
from uuid import UUID

# Pydantic 的 BaseModel，用于定义数据模型和自动数据验证
from pydantic import BaseModel


# 文件上传响应模型，用于定义文件上传成功后返回的数据结构
class UploadFileResponse(BaseModel):
    """File upload response schema."""

    id: UUID  # 文件的唯一标识符
    name: str  # 文件名称
    path: str  # 文件存储路径
    size: int  # 文件大小（字节）
    provider: str | None = None  # 文件提供者，可选字段，默认为 None
