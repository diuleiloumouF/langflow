# AI/ML API 模型组件
# 用于通过 AI/ML API 调用大语言模型生成文本

from langchain_openai import ChatOpenAI
from pydantic.v1 import SecretStr
from typing_extensions import override

from lfx.base.models.aiml_constants import AimlModels
from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import (
    DictInput,
    DropdownInput,
    IntInput,
    SecretStrInput,
    SliderInput,
    StrInput,
)


# AI/ML API 模型组件类
# 继承自 LCModelComponent，封装了 AI/ML API 的调用逻辑
# 支持配置模型名称、API 密钥、温度等参数
class AIMLModelComponent(LCModelComponent):
    display_name = "AI/ML API"
    description = "Generates text using AI/ML API LLMs."
    icon = "AIML"
    name = "AIMLModel"
    documentation = "https://docs.aimlapi.com/api-reference"

    # 组件输入参数定义
    # 包含基础模型输入参数、最大 token 数、模型参数、模型名称、API 基础地址、API 密钥和温度
    inputs = [
        *LCModelComponent.get_base_inputs(),
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            info="The maximum number of tokens to generate. Set to 0 for unlimited tokens.",
            range_spec=RangeSpec(min=0, max=128000),
        ),
        DictInput(name="model_kwargs", display_name="Model Kwargs", advanced=True),
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            advanced=False,
            options=[],
            refresh_button=True,
        ),
        StrInput(
            name="aiml_api_base",
            display_name="AI/ML API Base",
            advanced=True,
            info="The base URL of the API. Defaults to https://api.aimlapi.com . "
            "You can change this to use other APIs like JinaChat, LocalAI and Prem.",
        ),
        SecretStrInput(
            name="api_key",
            display_name="AI/ML API Key",
            info="The AI/ML API Key to use for the OpenAI model.",
            advanced=False,
            value="AIML_API_KEY",
            required=True,
        ),
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            range_spec=RangeSpec(min=0, max=2, step=0.01),
        ),
    ]

    # 当 API 密钥、API 基础地址或模型名称发生变化时，动态刷新模型列表
    @override
    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        if field_name in {"api_key", "aiml_api_base", "model_name"}:
            aiml = AimlModels()
            aiml.get_aiml_models()
            build_config["model_name"]["options"] = aiml.chat_models
        return build_config

    # 构建并返回配置好的 ChatOpenAI 模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        aiml_api_key = self.api_key
        temperature = self.temperature
        model_name: str = self.model_name
        max_tokens = self.max_tokens
        model_kwargs = self.model_kwargs or {}
        aiml_api_base = self.aiml_api_base or "https://api.aimlapi.com/v2"

        openai_api_key = aiml_api_key.get_secret_value() if isinstance(aiml_api_key, SecretStr) else aiml_api_key

        # TODO: Once OpenAI fixes their o1 models, this part will need to be removed
        # to work correctly with o1 temperature settings.
        if "o1" in model_name:
            temperature = 1

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=openai_api_key,
            base_url=aiml_api_base,
            max_tokens=max_tokens or None,
            **model_kwargs,
        )

    # 从 OpenAI 异常中提取错误信息
    def _get_exception_message(self, e: Exception):
        """Get a message from an OpenAI exception.

        Args:
            e (Exception): The exception to get the message from.

        Returns:
            str: The message from the exception.
        """
        try:
            from openai.error import BadRequestError
        except ImportError:
            return None
        if isinstance(e, BadRequestError):
            message = e.json_body.get("error", {}).get("message", "")
            if message:
                return message
        return None
