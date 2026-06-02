# Vertex AI 嵌入模型组件，基于 Google Cloud Vertex AI 生成文本向量嵌入
from lfx.base.models.model import LCModelComponent
from lfx.field_typing import Embeddings
from lfx.io import BoolInput, FileInput, FloatInput, IntInput, MessageTextInput, Output


# 使用 Google Vertex AI 模型生成文本嵌入向量的组件
class VertexAIEmbeddingsComponent(LCModelComponent):
    # 组件显示名称
    display_name = "Vertex AI Embeddings"
    # 组件描述
    description = "Generate embeddings using Google Cloud Vertex AI models."
    # 组件图标
    icon = "VertexAI"
    # 组件内部名称
    name = "VertexAIEmbeddings"

    # 组件输入参数定义
    inputs = [
        # 凭证文件：JSON 格式的服务账号密钥文件（必填）
        FileInput(
            name="credentials",
            display_name="Credentials",
            info="JSON credentials file. Leave empty to fallback to environment variables",
            value="",
            file_types=["json"],
            required=True,
        ),
        # GCP 区域，默认为 us-central1
        MessageTextInput(name="location", display_name="Location", value="us-central1", advanced=True),
        # GCP 项目 ID
        MessageTextInput(name="project", display_name="Project", info="The project ID.", advanced=True),
        # 最大输出 token 数
        IntInput(name="max_output_tokens", display_name="Max Output Tokens", advanced=True),
        # 最大重试次数
        IntInput(name="max_retries", display_name="Max Retries", value=1, advanced=True),
        # 嵌入模型名称，默认使用 textembedding-gecko
        MessageTextInput(name="model_name", display_name="Model Name", value="textembedding-gecko", required=True),
        # 每次请求返回的嵌入数量
        IntInput(name="n", display_name="N", value=1, advanced=True),
        # 请求并行度，控制并发请求数量
        IntInput(name="request_parallelism", value=5, display_name="Request Parallelism", advanced=True),
        # 停止序列列表
        MessageTextInput(name="stop_sequences", display_name="Stop", advanced=True, is_list=True),
        # 是否启用流式输出
        BoolInput(name="streaming", display_name="Streaming", value=False, advanced=True),
        # 温度参数，控制生成随机性
        FloatInput(name="temperature", value=0.0, display_name="Temperature"),
        # Top-K 采样参数
        IntInput(name="top_k", display_name="Top K", advanced=True),
        # Top-P 采样参数
        FloatInput(name="top_p", display_name="Top P", value=0.95, advanced=True),
    ]

    # 组件输出定义
    outputs = [
        Output(display_name="Embeddings", name="embeddings", method="build_embeddings"),
    ]

    # 构建 Vertex AI 嵌入模型实例
    def build_embeddings(self) -> Embeddings:
        try:
            from langchain_google_vertexai import VertexAIEmbeddings
        except ImportError as e:
            msg = "Please install the langchain-google-vertexai package to use the VertexAIEmbeddings component."
            raise ImportError(msg) from e

        from google.oauth2 import service_account

        if self.credentials:
            # 从服务账号文件加载凭证
            gcloud_credentials = service_account.Credentials.from_service_account_file(self.credentials)
        else:
            # will fallback to environment variable or inferred from gcloud CLI
            # 未提供凭证文件时，回退到环境变量或 gcloud CLI 推断的凭证
            gcloud_credentials = None
        return VertexAIEmbeddings(
            credentials=gcloud_credentials,
            location=self.location,
            max_output_tokens=self.max_output_tokens or None,
            max_retries=self.max_retries,
            model_name=self.model_name,
            n=self.n,
            project=self.project,
            request_parallelism=self.request_parallelism,
            stop=self.stop_sequences or None,
            streaming=self.streaming,
            temperature=self.temperature,
            top_k=self.top_k or None,
            top_p=self.top_p,
        )
