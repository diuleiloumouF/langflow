# LangChain Azure OpenAI 嵌入模型集成
from langchain_openai import AzureOpenAIEmbeddings

# 模型组件基类、常量定义、类型定义、输入组件
from lfx.base.models.model import LCModelComponent
from lfx.base.models.openai_constants import OPENAI_EMBEDDING_MODEL_NAMES
from lfx.field_typing import Embeddings
from lfx.io import DropdownInput, IntInput, MessageTextInput, Output, SecretStrInput


# Azure OpenAI 嵌入模型组件，用于通过 Azure 平台生成文本嵌入向量
class AzureOpenAIEmbeddingsComponent(LCModelComponent):
    display_name: str = "Azure OpenAI Embeddings"
    # 组件描述：使用 Azure OpenAI 模型生成文本嵌入向量
    description: str = "Generate embeddings using Azure OpenAI models."
    documentation: str = "https://python.langchain.com/docs/integrations/text_embedding/azureopenai"
    icon = "Azure"
    name = "AzureOpenAIEmbeddings"

    # 支持的 API 版本选项列表
    API_VERSION_OPTIONS = [
        "2022-12-01",
        "2023-03-15-preview",
        "2023-05-15",
        "2023-06-01-preview",
        "2023-07-01-preview",
        "2023-08-01-preview",
    ]

    # 输入参数定义
    inputs = [
        # 嵌入模型选择下拉框
        DropdownInput(
            name="model",
            display_name="Model",
            advanced=False,
            options=OPENAI_EMBEDDING_MODEL_NAMES,
            value=OPENAI_EMBEDDING_MODEL_NAMES[0],
        ),
        # Azure 端点 URL
        MessageTextInput(
            name="azure_endpoint",
            display_name="Azure Endpoint",
            required=True,
            info="Your Azure endpoint, including the resource. Example: `https://example-resource.azure.openai.com/`",
        ),
        # Azure 部署名称
        MessageTextInput(
            name="azure_deployment",
            display_name="Deployment Name",
            required=True,
        ),
        # API 版本选择
        DropdownInput(
            name="api_version",
            display_name="API Version",
            options=API_VERSION_OPTIONS,
            value=API_VERSION_OPTIONS[-1],
            advanced=True,
        ),
        # Azure OpenAI API 密钥
        SecretStrInput(
            name="api_key",
            display_name="Azure OpenAI API Key",
            required=True,
        ),
        # 输出嵌入向量的维度数（仅部分模型支持）
        IntInput(
            name="dimensions",
            display_name="Dimensions",
            info="The number of dimensions the resulting output embeddings should have. "
            "Only supported by certain models.",
            advanced=True,
        ),
    ]

    # 输出参数：嵌入模型实例
    outputs = [
        Output(display_name="Embeddings", name="embeddings", method="build_embeddings"),
    ]

    # 构建并返回 Azure OpenAI 嵌入模型实例
    def build_embeddings(self) -> Embeddings:
        try:
            embeddings = AzureOpenAIEmbeddings(
                model=self.model,
                azure_endpoint=self.azure_endpoint,
                azure_deployment=self.azure_deployment,
                api_version=self.api_version,
                api_key=self.api_key,
                dimensions=self.dimensions or None,
            )
        except Exception as e:
            msg = f"Could not connect to AzureOpenAIEmbeddings API: {e}"
            raise ValueError(msg) from e

        return embeddings
