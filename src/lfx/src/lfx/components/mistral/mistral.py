# MistralAI 模型组件，用于集成 MistralAI 大语言模型
from langchain_mistralai import ChatMistralAI
from pydantic.v1 import SecretStr

from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.io import BoolInput, DropdownInput, FloatInput, IntInput, SecretStrInput, StrInput


class MistralAIModelComponent(LCModelComponent):
    """MistralAI 模型组件，基于 LangChain 的 ChatMistralAI 封装，支持多种 Mistral 模型。

    该组件继承自 LCModelComponent，提供了对 MistralAI API 的完整集成，
    包括模型选择、API 密钥管理、超时设置等配置项。
    """

    # 组件在画布上显示的名称
    display_name = "MistralAI"
    # 组件描述信息，说明该组件使用 MistralAI LLM 生成文本
    description = "Generates text using MistralAI LLMs."
    # 组件图标
    icon = "MistralAI"
    # 组件内部标识名称
    name = "MistralModel"

    # 组件输入参数定义列表，包含基础输入参数和 MistralAI 特有参数
    inputs = [
        *LCModelComponent.get_base_inputs(),  # 继承基础模型组件的输入参数（如 stream 等）
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            # 最大 token 生成数量，设为 0 表示不限制
            info="The maximum number of tokens to generate. Set to 0 for unlimited tokens.",
        ),
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            advanced=False,
            # 可选的 Mistral 模型列表
            options=[
                "open-mixtral-8x7b",
                "open-mixtral-8x22b",
                "mistral-small-latest",
                "mistral-medium-latest",
                "mistral-large-latest",
                "codestral-latest",
            ],
            value="codestral-latest",  # 默认使用 codestral-latest 模型
        ),
        StrInput(
            name="mistral_api_base",
            display_name="Mistral API Base",
            advanced=True,
            # Mistral API 基础地址，支持自定义以使用其他兼容 API（如 JinaChat、LocalAI 等）
            info="The base URL of the Mistral API. Defaults to https://api.mistral.ai/v1. "
            "You can change this to use other APIs like JinaChat, LocalAI and Prem.",
        ),
        SecretStrInput(
            name="api_key",
            display_name="Mistral API Key",
            info="The Mistral API Key to use for the Mistral model.",
            advanced=False,
            required=True,
            value="MISTRAL_API_KEY",  # 默认从环境变量 MISTRAL_API_KEY 读取
        ),
        FloatInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,  # 默认温度值，较低的值产生更确定性的输出
            advanced=True,
        ),
        IntInput(
            name="max_retries",
            display_name="Max Retries",
            advanced=True,
            value=5,  # 最大重试次数
        ),
        IntInput(
            name="timeout",
            display_name="Timeout",
            advanced=True,
            value=60,  # 请求超时时间（秒）
        ),
        IntInput(
            name="max_concurrent_requests",
            display_name="Max Concurrent Requests",
            advanced=True,
            value=3,  # 最大并发请求数
        ),
        FloatInput(
            name="top_p",
            display_name="Top P",
            advanced=True,
            value=1,  # Top-P 采样参数，控制输出多样性
        ),
        IntInput(
            name="random_seed",
            display_name="Random Seed",
            value=1,  # 随机种子，用于结果可复现
            advanced=True,
        ),
        BoolInput(
            name="safe_mode",
            display_name="Safe Mode",
            advanced=True,
            value=False,  # 安全模式开关，启用后会过滤敏感内容
        ),
    ]

    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        """构建并返回 MistralAI 聊天模型实例。

        根据组件配置的参数创建 ChatMistralAI 实例。
        如果连接失败，将抛出 ValueError 异常。

        Returns:
            LanguageModel: 配置好的 MistralAI 语言模型实例。

        Raises:
            ValueError: 当无法连接到 MistralAI API 时抛出。
        """
        try:
            return ChatMistralAI(
                model_name=self.model_name,
                # 如果提供了 API 密钥则进行解密，否则传递 None
                mistral_api_key=SecretStr(self.api_key).get_secret_value() if self.api_key else None,
                # API 端点地址，默认为 Mistral 官方 API
                endpoint=self.mistral_api_base or "https://api.mistral.ai/v1",
                # max_tokens 为 0 时视为不限制，传 None
                max_tokens=self.max_tokens or None,
                temperature=self.temperature,
                max_retries=self.max_retries,
                timeout=self.timeout,
                max_concurrent_requests=self.max_concurrent_requests,
                top_p=self.top_p,
                random_seed=self.random_seed,
                safe_mode=self.safe_mode,
                streaming=self.stream,  # 使用父组件的 stream 参数控制流式输出
            )
        except Exception as e:
            msg = "Could not connect to MistralAI API."
            raise ValueError(msg) from e
