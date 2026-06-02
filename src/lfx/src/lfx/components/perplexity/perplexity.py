from langchain_perplexity import ChatPerplexity
from pydantic.v1 import SecretStr

from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.io import DropdownInput, FloatInput, IntInput, SecretStrInput, SliderInput


# Perplexity 大语言模型组件，用于在 Langflow 流程中接入 Perplexity API 进行文本生成
class PerplexityComponent(LCModelComponent):
    display_name = "Perplexity"
    description = "Generate text using Perplexity LLMs."
    documentation = "https://python.langchain.com/v0.2/docs/integrations/chat/perplexity/"
    icon = "Perplexity"
    name = "PerplexityModel"

    # 组件输入参数定义，包含模型选择、API 密钥、温度等配置
    inputs = [
        *LCModelComponent.get_base_inputs(),
        # 模型名称下拉选择框，支持多种 Perplexity 模型（sonar 系列和 llama 指令微调系列）
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            advanced=False,
            options=[
                "llama-3.1-sonar-small-128k-online",
                "llama-3.1-sonar-large-128k-online",
                "llama-3.1-sonar-huge-128k-online",
                "llama-3.1-sonar-small-128k-chat",
                "llama-3.1-sonar-large-128k-chat",
                "llama-3.1-8b-instruct",
                "llama-3.1-70b-instruct",
            ],
            value="llama-3.1-sonar-small-128k-online",
        ),
        # 最大输出 token 数量
        IntInput(name="max_tokens", display_name="Max Output Tokens", info="The maximum number of tokens to generate."),
        # Perplexity API 密钥，必填项
        SecretStrInput(
            name="api_key",
            display_name="Perplexity API Key",
            info="The Perplexity API Key to use for the Perplexity model.",
            advanced=False,
            required=True,
        ),
        # 温度参数滑块，控制生成文本的随机性，范围 0-2，默认 0.75
        SliderInput(
            name="temperature", display_name="Temperature", value=0.75, range_spec=RangeSpec(min=0, max=2, step=0.05)
        ),
        # Top P 采样参数，控制采样时考虑的 token 累积概率上限
        FloatInput(
            name="top_p",
            display_name="Top P",
            info="The maximum cumulative probability of tokens to consider when sampling.",
            advanced=True,
        ),
        # 每个提示生成的补全数量，API 可能因去重而返回少于指定数量的结果
        IntInput(
            name="n",
            display_name="N",
            info="Number of chat completions to generate for each prompt. "
            "Note that the API may not return the full n completions if duplicates are generated.",
            advanced=True,
        ),
    ]

    # 构建并返回 Perplexity 聊天模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        api_key = SecretStr(self.api_key).get_secret_value()
        temperature = self.temperature
        model = self.model_name
        max_tokens = self.max_tokens
        top_p = self.top_p
        n = self.n

        return ChatPerplexity(
            model=model,
            temperature=temperature or 0.75,
            pplx_api_key=api_key,
            top_p=top_p or None,
            n=n or 1,
            max_tokens=max_tokens,
        )
