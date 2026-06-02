# LangChain Azure OpenAI 聊天模型集成
from langchain_openai import AzureChatOpenAI

# 模型组件基类、类型定义、输入组件
from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import MessageTextInput
from lfx.io import DropdownInput, IntInput, SecretStrInput, SliderInput


# Azure OpenAI 聊天模型组件，用于通过 Azure 平台调用 OpenAI 大语言模型生成文本
class AzureChatOpenAIComponent(LCModelComponent):
    display_name: str = "Azure OpenAI"
    # 组件描述：使用 Azure OpenAI 大语言模型生成文本
    description: str = "Generate text using Azure OpenAI LLMs."
    documentation: str = "https://python.langchain.com/docs/integrations/llms/azure_openai"
    beta = False
    icon = "Azure"
    name = "AzureOpenAIModel"

    # Azure OpenAI 支持的 API 版本列表
    AZURE_OPENAI_API_VERSIONS = [
        "2024-06-01",
        "2024-07-01-preview",
        "2024-08-01-preview",
        "2024-09-01-preview",
        "2024-10-01-preview",
        "2023-05-15",
        "2023-12-01-preview",
        "2024-02-15-preview",
        "2024-03-01-preview",
        "2024-12-01-preview",
        "2025-01-01-preview",
        "2025-02-01-preview",
    ]

    # 输入参数定义（继承基础模型输入 + Azure 特有参数）
    inputs = [
        *LCModelComponent.get_base_inputs(),
        # Azure 端点 URL，包含资源名称
        MessageTextInput(
            name="azure_endpoint",
            display_name="Azure Endpoint",
            info="Your Azure endpoint, including the resource. Example: `https://example-resource.azure.openai.com/`",
            required=True,
        ),
        # Azure 部署名称
        MessageTextInput(name="azure_deployment", display_name="Deployment Name", required=True),
        # Azure OpenAI API 密钥
        SecretStrInput(name="api_key", display_name="Azure Chat OpenAI API Key", required=True),
        # API 版本选择下拉框，按降序排列
        DropdownInput(
            name="api_version",
            display_name="API Version",
            options=sorted(AZURE_OPENAI_API_VERSIONS, reverse=True),
            value=next(
                (
                    version
                    for version in sorted(AZURE_OPENAI_API_VERSIONS, reverse=True)
                    if not version.endswith("-preview")
                ),
                AZURE_OPENAI_API_VERSIONS[0],
            ),
        ),
        # 温度参数滑块，控制输出随机性（0=确定性，2=高随机性）
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=1.0,
            range_spec=RangeSpec(min=0, max=2, step=0.01),
            info="Controls randomness. Lower values are more deterministic, higher values are more creative.",
            advanced=True,
        ),
        # 最大生成 token 数量（0 表示不限制）
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            info="The maximum number of tokens to generate. Set to 0 for unlimited tokens.",
        ),
    ]

    # 构建并返回 Azure OpenAI 聊天模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        azure_endpoint = self.azure_endpoint
        azure_deployment = self.azure_deployment
        api_version = self.api_version
        api_key = self.api_key
        temperature = self.temperature
        max_tokens = self.max_tokens
        stream = self.stream

        try:
            output = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                azure_deployment=azure_deployment,
                api_version=api_version,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens or None,
                streaming=stream,
            )
        except Exception as e:
            msg = f"Could not connect to AzureOpenAI API: {e}"
            raise ValueError(msg) from e

        return output
