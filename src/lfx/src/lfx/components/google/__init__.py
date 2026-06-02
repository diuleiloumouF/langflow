# Google 组件包：提供与 Google 各项服务集成的 Langflow 组件
from .gmail import GmailLoaderComponent  # Gmail 邮件加载器组件，用于读取和解析 Gmail 邮件
from .google_bq_sql_executor import (
    BigQueryExecutorComponent,  # BigQuery SQL 执行器组件，用于在 Google BigQuery 上运行 SQL 查询
)
from .google_drive import GoogleDriveComponent  # Google Drive 文件操作组件，用于读取和管理 Google Drive 中的文件
from .google_drive_search import GoogleDriveSearchComponent  # Google Drive 搜索组件，用于在 Google Drive 中搜索文件
from .google_generative_ai import (
    GoogleGenerativeAIComponent,  # Google 生成式 AI 组件（Gemini），用于调用 Google 的大语言模型
)
from .google_generative_ai_embeddings import (
    GoogleGenerativeAIEmbeddingsComponent,  # Google 生成式 AI 嵌入组件，用于生成文本向量嵌入
)
from .google_oauth_token import GoogleOAuthToken  # Google OAuth 令牌组件，用于获取和管理 Google OAuth 认证令牌

__all__ = [
    "BigQueryExecutorComponent",  # BigQuery SQL 执行器
    "GmailLoaderComponent",  # Gmail 邮件加载器
    "GoogleDriveComponent",  # Google Drive 文件操作
    "GoogleDriveSearchComponent",  # Google Drive 搜索
    "GoogleGenerativeAIComponent",  # Google 生成式 AI（Gemini）
    "GoogleGenerativeAIEmbeddingsComponent",  # Google 生成式 AI 嵌入
    "GoogleOAuthToken",  # Google OAuth 令牌
]
