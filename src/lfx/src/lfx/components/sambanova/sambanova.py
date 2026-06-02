from langchain_sambanova import ChatSambaNovaCloud
from pydantic.v1 import SecretStr

from lfx.base.models.model import LCModelComponent
from lfx.base.models.sambanova_constants import SAMBANOVA_MODEL_NAMES
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.io import DropdownInput, IntInput, SecretStrInput, SliderInput, StrInput


# SambaNova 模型组件，使用 SambaNova 的 LLM 生成文本
class SambaNovaComponent(LCModelComponent):
    # 组件显示名称
    display_name = "SambaNova"
    # 组件描述信息
    description = "Generate text using Sambanova LLMs."
    # 组件文档链接
    documentation = "https://cloud.sambanova.ai/"
    # 组件图标
    icon = "SambaNova"
    # 组件内部名称
    name = "SambaNovaModel"

    # 组件输入参数定义
    inputs = [
        *LCModelComponent.get_base_inputs(),
        StrInput(
            name="base_url",
            display_name="SambaNova Cloud Base Url",
            advanced=True,
            info="The base URL of the Sambanova Cloud API. "
            "Defaults to https://api.sambanova.ai/v1/chat/completions. "
            "You can change this to use other urls like Sambastudio",
        ),
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            advanced=False,
            options=SAMBANOVA_MODEL_NAMES,
            value=SAMBANOVA_MODEL_NAMES[0],
        ),
        SecretStrInput(
            name="api_key",
            display_name="Sambanova API Key",
            info="The Sambanova API Key to use for the Sambanova model.",
            advanced=False,
            value="SAMBANOVA_API_KEY",
            required=True,
        ),
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            value=2048,
            info="The maximum number of tokens to generate.",
        ),
        SliderInput(
            name="top_p",
            display_name="top_p",
            advanced=True,
            value=1.0,
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            info="Model top_p",
        ),
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            range_spec=RangeSpec(min=0, max=2, step=0.01),
            advanced=True,
        ),
    ]

    # 构建 ChatSambaNovaCloud 模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        sambanova_url = self.base_url
        sambanova_api_key = self.api_key
        model_name = self.model_name
        max_tokens = self.max_tokens
        top_p = self.top_p
        temperature = self.temperature

        api_key = SecretStr(sambanova_api_key).get_secret_value() if sambanova_api_key else None

        return ChatSambaNovaCloud(
            model=model_name,
            max_tokens=max_tokens or 1024,
            temperature=temperature or 0.07,
            top_p=top_p,
            sambanova_url=sambanova_url,
            sambanova_api_key=api_key,
        )
