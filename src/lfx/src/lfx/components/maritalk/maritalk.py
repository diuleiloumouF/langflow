from langchain_community.chat_models import ChatMaritalk

from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import DropdownInput, FloatInput, IntInput, SecretStrInput


# MariTalk 模型组件，用于集成巴西 MariTalk 大语言模型
class MaritalkModelComponent(LCModelComponent):
    # 组件显示名称
    display_name = "MariTalk"
    # 组件描述
    description = "Generates text using MariTalk LLMs."
    # 组件图标
    icon = "Maritalk"
    # 组件内部名称
    name = "Maritalk"
    # 组件输入参数定义
    inputs = [
        # 继承父类的基础输入参数（如 llm_model、stream 等）
        *LCModelComponent.get_base_inputs(),
        # 最大生成 token 数量，设为 0 表示无限制
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            value=512,
            info="The maximum number of tokens to generate. Set to 0 for unlimited tokens.",
        ),
        # 模型名称选择，支持 sabia-2-small 和 sabia-2-medium 两种型号
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            advanced=False,
            options=["sabia-2-small", "sabia-2-medium"],
            value=["sabia-2-small"],
        ),
        # MariTalk API 密钥，用于身份验证
        SecretStrInput(
            name="api_key",
            display_name="MariTalk API Key",
            info="The MariTalk API Key to use for authentication.",
            advanced=False,
        ),
        # 生成温度参数，控制输出的随机性，范围 0-1
        FloatInput(name="temperature", display_name="Temperature", value=0.1, range_spec=RangeSpec(min=0, max=1)),
    ]

    # 构建并返回 MariTalk 模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        # self.output_schea is a list of dictionarie s
        # let's convert it to a dictionary
        # 获取组件配置的各个参数值
        api_key = self.api_key
        temperature = self.temperature
        model_name: str = self.model_name
        max_tokens = self.max_tokens

        # 创建并返回 ChatMaritalk 模型实例，默认温度为 0.1
        return ChatMaritalk(
            max_tokens=max_tokens,
            model=model_name,
            api_key=api_key,
            temperature=temperature or 0.1,
        )
