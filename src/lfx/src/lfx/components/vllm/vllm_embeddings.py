# vLLM 嵌入模型组件，通过 OpenAI 兼容 API 调用 vLLM 推理服务器生成文本嵌入
from langchain_openai import OpenAIEmbeddings

from lfx.base.embeddings.model import LCEmbeddingsModel
from lfx.field_typing import Embeddings
from lfx.io import BoolInput, DictInput, FloatInput, IntInput, MessageTextInput, SecretStrInput


# 使用 vLLM 模型通过 OpenAI 兼容 API 生成文本嵌入向量的组件
class VllmEmbeddingsComponent(LCEmbeddingsModel):
    # 组件显示名称
    display_name = "vLLM Embeddings"
    # 组件描述
    description = "Generate embeddings using vLLM models via OpenAI-compatible API."
    # 组件图标
    icon = "vLLM"
    # 组件内部名称
    name = "vLLMEmbeddings"

    # 组件输入参数定义
    inputs = [
        # 嵌入模型名称
        MessageTextInput(
            name="model_name",
            display_name="Model Name",
            advanced=False,
            info="The name of the vLLM embeddings model to use (e.g., 'BAAI/bge-large-en-v1.5').",
            value="BAAI/bge-large-en-v1.5",
        ),
        # vLLM API 服务器基础 URL
        MessageTextInput(
            name="api_base",
            display_name="vLLM API Base",
            advanced=False,
            info="The base URL of the vLLM API server. Defaults to http://localhost:8000/v1 for local vLLM server.",
            value="http://localhost:8000/v1",
        ),
        # API 密钥（本地服务器可选）
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            info="The API Key to use for the vLLM model (optional for local servers).",
            advanced=False,
            value="",
            required=False,
        ),
        # 输出嵌入向量的维度数（仅部分模型支持）
        IntInput(
            name="dimensions",
            display_name="Dimensions",
            info="The number of dimensions the resulting output embeddings should have. "
            "Only supported by certain models.",
            advanced=True,
        ),
        # 文档处理时的分块大小
        IntInput(
            name="chunk_size",
            display_name="Chunk Size",
            advanced=True,
            value=1000,
            info="The chunk size to use when processing documents.",
        ),
        # 最大重试次数
        IntInput(
            name="max_retries",
            display_name="Max Retries",
            value=3,
            advanced=True,
            info="Maximum number of retries for failed requests.",
        ),
        # 请求超时时间（秒）
        FloatInput(
            name="request_timeout",
            display_name="Request Timeout",
            advanced=True,
            info="Timeout for requests to vLLM API in seconds.",
        ),
        # 是否显示处理进度条
        BoolInput(
            name="show_progress_bar",
            display_name="Show Progress Bar",
            advanced=True,
            info="Whether to show a progress bar when processing multiple documents.",
        ),
        # 是否跳过空文档
        BoolInput(
            name="skip_empty",
            display_name="Skip Empty",
            advanced=True,
            info="Whether to skip empty documents.",
        ),
        # 传递给模型的额外关键字参数
        DictInput(
            name="model_kwargs",
            display_name="Model Kwargs",
            advanced=True,
            info="Additional keyword arguments to pass to the model.",
        ),
        # API 请求的默认请求头
        DictInput(
            name="default_headers",
            display_name="Default Headers",
            advanced=True,
            info="Default headers to use for the API request.",
        ),
        # API 请求的默认查询参数
        DictInput(
            name="default_query",
            display_name="Default Query",
            advanced=True,
            info="Default query parameters to use for the API request.",
        ),
    ]

    # 构建 vLLM 嵌入模型实例
    def build_embeddings(self) -> Embeddings:
        return OpenAIEmbeddings(
            model=self.model_name,
            base_url=self.api_base or "http://localhost:8000/v1",
            api_key=self.api_key or None,
            dimensions=self.dimensions or None,
            chunk_size=self.chunk_size,
            max_retries=self.max_retries,
            timeout=self.request_timeout or None,
            show_progress_bar=self.show_progress_bar,
            skip_empty=self.skip_empty,
            model_kwargs=self.model_kwargs,
            default_headers=self.default_headers or None,
            default_query=self.default_query or None,
        )
