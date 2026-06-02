# OpenAI Embeddings 组件模块
# 本模块提供 OpenAI 嵌入模型的 Langflow 组件实现
from langchain_openai import OpenAIEmbeddings

from lfx.base.embeddings.model import LCEmbeddingsModel
from lfx.base.models.openai_constants import OPENAI_EMBEDDING_MODEL_NAMES
from lfx.field_typing import Embeddings
from lfx.io import BoolInput, DictInput, DropdownInput, FloatInput, IntInput, MessageTextInput, SecretStrInput


# OpenAI Embeddings 组件类
# 继承自 LCEmbeddingsModel，提供 OpenAI 文本嵌入功能
class OpenAIEmbeddingsComponent(LCEmbeddingsModel):
    # 组件在 UI 中显示的名称
    display_name = "OpenAI Embeddings"
    # 组件的描述信息
    description = "Generate embeddings using OpenAI models."
    # 组件图标
    icon = "OpenAI"
    # 组件内部唯一标识名称
    name = "OpenAIEmbeddings"

    # 组件输入参数定义列表
    inputs = [
        # 默认请求头配置（高级参数）
        DictInput(
            name="default_headers",
            display_name="Default Headers",
            advanced=True,
            # Default headers to use for the API request.
            info="Default headers to use for the API request.",
        ),
        # 默认查询参数配置（高级参数）
        DictInput(
            name="default_query",
            display_name="Default Query",
            advanced=True,
            # Default query parameters to use for the API request.
            info="Default query parameters to use for the API request.",
        ),
        # 分块大小，用于处理长文本时的分块处理
        IntInput(name="chunk_size", display_name="Chunk Size", advanced=True, value=1000),
        # 客户端实例（高级参数）
        MessageTextInput(name="client", display_name="Client", advanced=True),
        # 部署名称（高级参数）
        MessageTextInput(name="deployment", display_name="Deployment", advanced=True),
        # 嵌入上下文长度，决定文本分块的最大长度
        IntInput(name="embedding_ctx_length", display_name="Embedding Context Length", advanced=True, value=1536),
        # 最大重试次数，API 请求失败时的重试次数
        IntInput(name="max_retries", display_name="Max Retries", value=3, advanced=True),
        # 模型选择下拉框，默认使用 text-embedding-3-small
        DropdownInput(
            name="model",
            display_name="Model",
            advanced=False,
            options=OPENAI_EMBEDDING_MODEL_NAMES,
            value="text-embedding-3-small",
        ),
        # 模型额外参数（高级参数）
        DictInput(name="model_kwargs", display_name="Model Kwargs", advanced=True),
        # OpenAI API 密钥（必填）
        SecretStrInput(name="openai_api_key", display_name="OpenAI API Key", value="OPENAI_API_KEY", required=True),
        # OpenAI API 基础 URL（高级参数，用于自定义端点）
        MessageTextInput(name="openai_api_base", display_name="OpenAI API Base", advanced=True),
        # OpenAI API 类型（高级参数）
        MessageTextInput(name="openai_api_type", display_name="OpenAI API Type", advanced=True),
        # OpenAI API 版本（高级参数）
        MessageTextInput(name="openai_api_version", display_name="OpenAI API Version", advanced=True),
        # OpenAI 组织 ID（高级参数）
        MessageTextInput(
            name="openai_organization",
            display_name="OpenAI Organization",
            advanced=True,
        ),
        # OpenAI 代理服务器（高级参数）
        MessageTextInput(name="openai_proxy", display_name="OpenAI Proxy", advanced=True),
        # 请求超时时间（秒）
        FloatInput(name="request_timeout", display_name="Request Timeout", advanced=True),
        # 是否显示进度条
        BoolInput(name="show_progress_bar", display_name="Show Progress Bar", advanced=True),
        # 是否跳过空文本
        BoolInput(name="skip_empty", display_name="Skip Empty", advanced=True),
        # TikToken 模型名称（高级参数）
        MessageTextInput(
            name="tiktoken_model_name",
            display_name="TikToken Model Name",
            advanced=True,
        ),
        # 是否启用 TikToken 分词器
        BoolInput(
            name="tiktoken_enable",
            display_name="TikToken Enable",
            advanced=True,
            value=True,
            # If False, you must have transformers installed.
            info="If False, you must have transformers installed.",
        ),
        # 输出嵌入的维度数，仅部分模型支持
        IntInput(
            name="dimensions",
            display_name="Dimensions",
            # The number of dimensions the resulting output embeddings should have.
            # Only supported by certain models.
            info="The number of dimensions the resulting output embeddings should have. "
            "Only supported by certain models.",
            advanced=True,
        ),
    ]

    # 构建 OpenAI Embeddings 实例
    # 将组件配置参数传递给 LangChain 的 OpenAIEmbeddings 类
    def build_embeddings(self) -> Embeddings:
        return OpenAIEmbeddings(
            client=self.client or None,
            model=self.model,
            dimensions=self.dimensions or None,
            deployment=self.deployment or None,
            api_version=self.openai_api_version or None,
            base_url=self.openai_api_base or None,
            openai_api_type=self.openai_api_type or None,
            openai_proxy=self.openai_proxy or None,
            embedding_ctx_length=self.embedding_ctx_length,
            api_key=self.openai_api_key or None,
            organization=self.openai_organization or None,
            allowed_special="all",
            disallowed_special="all",
            chunk_size=self.chunk_size,
            max_retries=self.max_retries,
            timeout=self.request_timeout or None,
            tiktoken_enabled=self.tiktoken_enable,
            tiktoken_model_name=self.tiktoken_model_name or None,
            show_progress_bar=self.show_progress_bar,
            model_kwargs=self.model_kwargs,
            skip_empty=self.skip_empty,
            default_headers=self.default_headers or None,
            default_query=self.default_query or None,
        )
