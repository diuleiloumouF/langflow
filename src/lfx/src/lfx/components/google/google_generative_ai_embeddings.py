from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output, SecretStrInput


class GoogleGenerativeAIEmbeddingsComponent(Component):
    # Google Generative AI 嵌入组件，用于连接 Google 的生成式 AI 嵌入服务
    display_name = "Google Generative AI Embeddings"
    # 通过 langchain-google-genai 包中的 GoogleGenerativeAIEmbeddings 类连接 Google 的生成式 AI 嵌入服务
    description = (
        "Connect to Google's generative AI embeddings service using the GoogleGenerativeAIEmbeddings class, "
        "found in the langchain-google-genai package."
    )
    # 官方文档链接
    documentation: str = "https://python.langchain.com/v0.2/docs/integrations/text_embedding/google_generative_ai/"
    # 组件图标
    icon = "GoogleGenerativeAI"
    # 组件内部名称
    name = "Google Generative AI Embeddings"

    # 组件输入参数定义
    inputs = [
        # Google Generative AI API 密钥，必填
        SecretStrInput(name="api_key", display_name="Google Generative AI API Key", required=True),
        # 嵌入模型名称，默认使用 text-embedding-004 模型
        MessageTextInput(name="model_name", display_name="Model Name", value="models/text-embedding-004"),
    ]

    # 组件输出定义
    outputs = [
        # 输出嵌入对象，通过 build_embeddings 方法构建
        Output(display_name="Embeddings", name="embeddings", method="build_embeddings"),
    ]

    def build_embeddings(self) -> Embeddings:
        # 构建并返回 Google Generative AI 嵌入实例
        if not self.api_key:
            msg = "API Key is required"
            raise ValueError(msg)

        return GoogleGenerativeAIEmbeddings(
            model=self.model_name,
            google_api_key=self.api_key,
        )
