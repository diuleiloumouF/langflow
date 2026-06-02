import requests
from langchain_openai import ChatOpenAI
from pydantic.v1 import SecretStr
from typing_extensions import override

from lfx.base.models.model import LCModelComponent
from lfx.base.models.novita_constants import MODEL_NAMES
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import (
    BoolInput,
    DictInput,
    DropdownInput,
    HandleInput,
    IntInput,
    SecretStrInput,
    SliderInput,
)


# Novita AI 模型组件，使用 Novita AI 的 LLM 生成文本（兼容 OpenAI 接口）
class NovitaModelComponent(LCModelComponent):
    # 组件显示名称
    display_name = "Novita AI"
    # 组件描述信息
    description = "Generates text using Novita AI LLMs (OpenAI compatible)."
    # 组件图标
    icon = "Novita"
    # 组件内部名称
    name = "NovitaModel"

    # 组件输入参数定义
    inputs = [
        *LCModelComponent.get_base_inputs(),
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            info="The maximum number of tokens to generate. Set to 0 for unlimited tokens.",
            range_spec=RangeSpec(min=0, max=128000),
        ),
        DictInput(
            name="model_kwargs",
            display_name="Model Kwargs",
            advanced=True,
            info="Additional keyword arguments to pass to the model.",
        ),
        BoolInput(
            name="json_mode",
            display_name="JSON Mode",
            advanced=True,
            info="If True, it will output JSON regardless of passing a schema.",
        ),
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            advanced=False,
            options=MODEL_NAMES,
            value=MODEL_NAMES[0],
            refresh_button=True,
        ),
        SecretStrInput(
            name="api_key",
            display_name="Novita API Key",
            info="The Novita API Key to use for Novita AI models.",
            advanced=False,
            value="NOVITA_API_KEY",
            real_time_refresh=True,
        ),
        SliderInput(name="temperature", display_name="Temperature", value=0.1, range_spec=RangeSpec(min=0, max=1)),
        IntInput(
            name="seed",
            display_name="Seed",
            info="The seed controls the reproducibility of the job.",
            advanced=True,
            value=1,
        ),
        HandleInput(
            name="output_parser",
            display_name="Output Parser",
            info="The parser to use to parse the output of the model",
            advanced=True,
            input_types=["OutputParser"],
        ),
    ]

    # 从 Novita AI API 获取可用的模型列表
    def get_models(self) -> list[str]:
        base_url = "https://api.novita.ai/v3/openai"
        url = f"{base_url}/models"

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            model_list = response.json()
            return [model["id"] for model in model_list.get("data", [])]
        except requests.RequestException as e:
            self.status = f"Error fetching models: {e}"
            return MODEL_NAMES

    # 更新构建配置，当 API 密钥或模型名称改变时刷新模型列表
    @override
    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        if field_name in {"api_key", "model_name"}:
            models = self.get_models()
            build_config["model_name"]["options"] = models
        return build_config

    # 构建 ChatOpenAI 模型实例，连接 Novita AI 服务
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        api_key = self.api_key
        temperature = self.temperature
        model_name: str = self.model_name
        max_tokens = self.max_tokens
        model_kwargs = self.model_kwargs or {}
        json_mode = self.json_mode
        seed = self.seed

        try:
            output = ChatOpenAI(
                model=model_name,
                api_key=(SecretStr(api_key).get_secret_value() if api_key else None),
                max_tokens=max_tokens or None,
                temperature=temperature,
                model_kwargs=model_kwargs,
                streaming=self.stream,
                seed=seed,
                base_url="https://api.novita.ai/v3/openai",
            )
        except Exception as e:
            msg = "Could not connect to Novita API."
            raise ValueError(msg) from e

        if json_mode:
            output = output.bind(response_format={"type": "json_object"})

        return output
