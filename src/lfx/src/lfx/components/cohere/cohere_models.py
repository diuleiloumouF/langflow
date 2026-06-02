# Cohere 聊天模型的 LangChain 集成
from langchain_cohere import ChatCohere

# Pydantic v1 的 SecretStr 用于安全存储 API 密钥
from pydantic.v1 import SecretStr

# 模型组件基类
from lfx.base.models.model import LCModelComponent

# 语言模型类型
from lfx.field_typing import LanguageModel

# 范围规范，用于定义滑块输入的范围
from lfx.field_typing.range_spec import RangeSpec

# 输入组件类型
from lfx.io import SecretStrInput, SliderInput


# Cohere 语言模型组件，用于文本生成
class CohereComponent(LCModelComponent):
    display_name = "Cohere Language Models"
    description = "Generate text using Cohere LLMs."
    documentation = "https://python.langchain.com/docs/integrations/llms/cohere/"
    icon = "Cohere"
    name = "CohereModel"

    # 输入参数定义
    inputs = [
        # 继承父类的基础输入参数
        *LCModelComponent.get_base_inputs(),
        # Cohere API 密钥
        SecretStrInput(
            name="cohere_api_key",
            display_name="Cohere API Key",
            info="The Cohere API Key to use for the Cohere model.",
            advanced=False,
            value="COHERE_API_KEY",
            required=True,
        ),
        # 温度参数：控制生成文本的随机性，值越低越确定，值越高越有创造性
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.75,
            range_spec=RangeSpec(min=0, max=2, step=0.01),
            info="Controls randomness. Lower values are more deterministic, higher values are more creative.",
            advanced=True,
        ),
    ]

    # 构建 Cohere 聊天模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        cohere_api_key = self.cohere_api_key
        temperature = self.temperature

        # 将 API 密钥转换为 SecretStr 格式
        api_key = SecretStr(cohere_api_key).get_secret_value() if cohere_api_key else None

        return ChatCohere(
            temperature=temperature or 0.75,
            cohere_api_key=api_key,
        )
