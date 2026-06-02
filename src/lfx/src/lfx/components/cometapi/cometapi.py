# CometAPI 组件模块
# 提供对 CometAPI 聚合大模型服务的 Langflow 集成，
# 底层通过 OpenAI 兼容协议访问 500+ 种 AI 模型。

import json

import requests
from langchain_openai import ChatOpenAI
from pydantic.v1 import SecretStr
from typing_extensions import override

from lfx.base.models.cometapi_constants import MODEL_NAMES
from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import (
    BoolInput,
    DictInput,
    DropdownInput,
    IntInput,
    SecretStrInput,
    SliderInput,
    StrInput,
)


class CometAPIComponent(LCModelComponent):
    """CometAPI component for language models."""

    # 在画布上显示的组件名称
    display_name = "CometAPI"
    # 组件描述信息，展示在组件面板中
    description = "All AI Models in One API 500+ AI Models"
    # 组件图标标识
    icon = "CometAPI"
    # 组件内部唯一名称
    name = "CometAPIModel"

    # 组件输入参数定义列表
    inputs = [
        # 继承自基类的基础输入参数（如 stream 等）
        *LCModelComponent.get_base_inputs(),
        # CometAPI 密钥输入，用于身份认证
        SecretStrInput(
            name="api_key",
            display_name="CometAPI Key",
            required=True,
            info="Your CometAPI key",
            real_time_refresh=True,
        ),
        # 应用名称，用于 CometAPI 排名统计
        StrInput(
            name="app_name",
            display_name="App Name",
            info="Your app name for CometAPI rankings",
            advanced=True,
        ),
        # 模型选择下拉框，选项通过 API 动态加载
        DropdownInput(
            name="model_name",
            display_name="Model",
            info="The model to use for chat completion",
            options=["Select a model"],
            value="Select a model",
            real_time_refresh=True,
            required=True,
        ),
        # 模型额外参数，以字典形式传递给底层模型
        DictInput(
            name="model_kwargs",
            display_name="Model Kwargs",
            info="Additional keyword arguments to pass to the model.",
            advanced=True,
        ),
        # 温度参数，控制生成结果的随机性
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.7,
            range_spec=RangeSpec(min=0, max=2, step=0.01),
            info="Controls randomness. Lower values are more deterministic, higher values are more creative.",
            advanced=True,
        ),
        # 最大生成 token 数
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            info="Maximum number of tokens to generate",
            advanced=True,
        ),
        # 随机种子，用于可复现的输出
        IntInput(
            name="seed",
            display_name="Seed",
            info="Seed for reproducible outputs.",
            value=1,
            advanced=True,
        ),
        # JSON 模式开关，启用后模型将返回 JSON 格式
        BoolInput(
            name="json_mode",
            display_name="JSON Mode",
            info="If enabled, the model will be asked to return a JSON object.",
            advanced=True,
        ),
    ]

    def get_models(self, token_override: str | None = None) -> list[str]:
        """从 CometAPI 获取可用模型列表。

        Args:
            token_override: 可选的 API 密钥覆盖值，用于在用户尚未保存密钥时
                            临时调用接口获取模型列表。

        Returns:
            可用模型 ID 列表；请求失败时回退到内置的默认模型列表。
        """
        # CometAPI 模型列表接口地址
        base_url = "https://api.cometapi.com/v1"
        url = f"{base_url}/models"

        headers = {"Content-Type": "application/json"}
        # Add Bearer Authorization when API key is available
        # 优先使用传入的覆盖密钥，否则使用已保存的密钥
        api_key_source = token_override if token_override else getattr(self, "api_key", None)
        if api_key_source:
            token = api_key_source.get_secret_value() if isinstance(api_key_source, SecretStr) else str(api_key_source)
            headers["Authorization"] = f"Bearer {token}"

        try:
            # 请求模型列表
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            # Safely parse JSON; fallback to defaults on failure
            # 安全解析 JSON 响应，解析失败则回退到默认模型列表
            try:
                model_list = response.json()
            except (json.JSONDecodeError, ValueError) as e:
                self.status = f"Error decoding models response: {e}"
                return MODEL_NAMES
            return [model["id"] for model in model_list.get("data", [])]
        except requests.RequestException as e:
            self.status = f"Error fetching models: {e}"
            # 网络请求失败时返回内置默认模型列表
            return MODEL_NAMES

    @override
    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        """动态更新组件构建配置。

        当用户输入新的 API 密钥时，自动刷新模型下拉框的可选项。

        Args:
            build_config: 当前构建配置字典。
            field_value: 被修改字段的新值。
            field_name: 被修改字段的名称。

        Returns:
            更新后的构建配置字典。
        """
        if field_name == "api_key":
            # 使用新密钥获取可用模型列表
            models = self.get_models(field_value)
            model_cfg = build_config.get("model_name", {})
            # Preserve placeholder (fallback to existing value or a generic prompt)
            # 保留占位符文本，优先使用已有值
            placeholder = model_cfg.get("placeholder", model_cfg.get("value", "Select a model"))
            current_value = model_cfg.get("value")

            options = list(models) if models else []
            # Ensure current value stays visible even if not present in fetched options
            # 确保当前选中的模型在列表中可见，即使它不在最新返回的列表中
            if current_value and current_value not in options:
                options = [current_value, *options]

            model_cfg["options"] = options
            model_cfg["placeholder"] = placeholder
            build_config["model_name"] = model_cfg
        return build_config

    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        """构建并返回 LangChain ChatOpenAI 实例。

        根据用户配置的参数（密钥、模型名、温度等）创建一个
        兼容 OpenAI 协议的聊天模型对象，供 Langflow 图引擎调用。

        Returns:
            配置好的 LangChain 语言模型实例。

        Raises:
            ValueError: 未选择有效模型或无法连接 CometAPI 时抛出。
        """
        api_key = self.api_key
        temperature = self.temperature
        model_name: str = self.model_name
        max_tokens = self.max_tokens
        model_kwargs = getattr(self, "model_kwargs", {}) or {}
        json_mode = self.json_mode
        seed = self.seed
        # Ensure a valid model was selected
        # 校验用户是否选择了有效的模型
        if not model_name or model_name == "Select a model":
            msg = "Please select a valid CometAPI model."
            raise ValueError(msg)
        try:
            # Extract raw API key safely
            # 安全提取明文 API 密钥
            _api_key = api_key.get_secret_value() if isinstance(api_key, SecretStr) else api_key
            output = ChatOpenAI(
                model=model_name,
                api_key=_api_key or None,
                max_tokens=max_tokens or None,
                temperature=temperature,
                model_kwargs=model_kwargs,
                streaming=bool(self.stream),
                seed=seed,
                # CometAPI 使用 OpenAI 兼容的接口地址
                base_url="https://api.cometapi.com/v1",
            )
        except (TypeError, ValueError) as e:
            msg = "Could not connect to CometAPI."
            raise ValueError(msg) from e

        # 若启用了 JSON 模式，绑定响应格式为 JSON
        if json_mode:
            output = output.bind(response_format={"type": "json_object"})

        return output
