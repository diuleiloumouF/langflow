# Vertex AI 聊天模型组件，基于 Google Cloud Vertex AI 平台生成文本
from typing import cast

from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.inputs.inputs import MessageTextInput
from lfx.io import BoolInput, FileInput, FloatInput, IntInput, StrInput


# 使用 Google Vertex AI LLM 生成文本的聊天模型组件
class ChatVertexAIComponent(LCModelComponent):
    # 组件显示名称
    display_name = "Vertex AI"
    # 组件描述
    description = "Generate text using Vertex AI LLMs."
    # 组件图标
    icon = "VertexAI"
    # 组件内部名称
    name = "VertexAiModel"

    # 组件输入参数定义
    inputs = [
        *LCModelComponent.get_base_inputs(),
        # 凭证文件：JSON 格式的服务账号密钥文件
        FileInput(
            name="credentials",
            display_name="Credentials",
            info="JSON credentials file. Leave empty to fallback to environment variables",
            file_types=["json"],
        ),
        # 模型名称，默认使用 gemini-1.5-pro
        MessageTextInput(name="model_name", display_name="Model Name", value="gemini-1.5-pro"),
        # GCP 项目 ID
        StrInput(name="project", display_name="Project", info="The project ID.", advanced=True),
        # GCP 区域，默认为 us-central1
        StrInput(name="location", display_name="Location", value="us-central1", advanced=True),
        # 最大输出 token 数
        IntInput(name="max_output_tokens", display_name="Max Output Tokens", advanced=True),
        # 最大重试次数
        IntInput(name="max_retries", display_name="Max Retries", value=1, advanced=True),
        # 温度参数，控制生成文本的随机性
        FloatInput(name="temperature", value=0.0, display_name="Temperature"),
        # Top-K 采样参数
        IntInput(name="top_k", display_name="Top K", advanced=True),
        # Top-P 采样参数
        FloatInput(name="top_p", display_name="Top P", value=0.95, advanced=True),
        # 是否输出详细日志
        BoolInput(name="verbose", display_name="Verbose", value=False, advanced=True),
    ]

    # 构建 Vertex AI 聊天模型实例
    def build_model(self) -> LanguageModel:
        try:
            from langchain_google_vertexai import ChatVertexAI
        except ImportError as e:
            msg = "Please install the langchain-google-vertexai package to use the VertexAIEmbeddings component."
            raise ImportError(msg) from e
        location = self.location or None
        if self.credentials:
            from google.cloud import aiplatform
            from google.oauth2 import service_account

            # 从服务账号文件加载凭证
            credentials = service_account.Credentials.from_service_account_file(self.credentials)
            project = self.project or credentials.project_id
            # ChatVertexAI sometimes skip manual credentials initialization
            # 手动初始化 AI Platform 以确保凭证正确传递
            aiplatform.init(
                project=project,
                location=location,
                credentials=credentials,
            )
        else:
            project = self.project or None
            credentials = None

        return cast(
            "LanguageModel",
            ChatVertexAI(
                credentials=credentials,
                location=location,
                project=project,
                max_output_tokens=self.max_output_tokens or None,
                max_retries=self.max_retries,
                model_name=self.model_name,
                temperature=self.temperature,
                top_k=self.top_k or None,
                top_p=self.top_p,
                verbose=self.verbose,
            ),
        )
