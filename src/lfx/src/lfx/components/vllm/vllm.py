# vLLM 聊天模型组件，通过 OpenAI 兼容 API 调用 vLLM 推理服务器生成文本
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic.v1 import SecretStr

from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import BoolInput, DictInput, IntInput, SecretStrInput, SliderInput, StrInput
from lfx.log.logger import logger


# 使用 vLLM 模型通过 OpenAI 兼容 API 生成文本的组件
class VllmComponent(LCModelComponent):
    # 组件显示名称
    display_name = "vLLM"
    # 组件描述
    description = "Generates text using vLLM models via OpenAI-compatible API."
    # 组件图标
    icon = "vLLM"
    # 组件内部名称
    name = "vLLMModel"

    # 组件输入参数定义
    inputs = [
        *LCModelComponent.get_base_inputs(),
        # 最大生成 token 数，设为 0 表示无限制
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            info="The maximum number of tokens to generate. Set to 0 for unlimited tokens.",
            range_spec=RangeSpec(min=0, max=128000),
        ),
        # 传递给模型的额外关键字参数
        DictInput(
            name="model_kwargs",
            display_name="Model Kwargs",
            advanced=True,
            info="Additional keyword arguments to pass to the model.",
        ),
        # JSON 模式：启用后无论是否传入 schema 都会输出 JSON
        BoolInput(
            name="json_mode",
            display_name="JSON Mode",
            advanced=True,
            info="If True, it will output JSON regardless of passing a schema.",
        ),
        # vLLM 模型名称
        StrInput(
            name="model_name",
            display_name="Model Name",
            advanced=False,
            info="The name of the vLLM model to use (e.g., 'ibm-granite/granite-3.3-8b-instruct').",
            value="ibm-granite/granite-3.3-8b-instruct",
        ),
        # vLLM API 服务器基础 URL
        StrInput(
            name="api_base",
            display_name="vLLM API Base",
            advanced=False,
            info="The base URL of the vLLM API server. Defaults to http://localhost:8000/v1 for local vLLM server.",
            value="http://localhost:8000/v1",
        ),
        # API 密钥（本地服务器可选）
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            info="The API Key to use for the vLLM model (optional for local servers).",
            advanced=False,
            value="",
            required=False,
        ),
        # 温度参数，控制生成随机性
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            show=True,
        ),
        # 随机种子，用于控制可复现性，-1 表示禁用
        IntInput(
            name="seed",
            display_name="Seed",
            info="Controls the reproducibility of the job. Set to -1 to disable (some providers may not support).",
            advanced=True,
            value=-1,
            required=False,
        ),
        # 最大重试次数，-1 表示禁用
        IntInput(
            name="max_retries",
            display_name="Max Retries",
            info="Max retries when generating. Set to -1 to disable (some providers may not support).",
            advanced=True,
            value=-1,
            required=False,
        ),
        # 请求超时时间（秒），-1 表示禁用
        IntInput(
            name="timeout",
            display_name="Timeout",
            info="Timeout for requests to vLLM completion API. Set to -1 to disable (some providers may not support).",
            advanced=True,
            value=-1,
            required=False,
        ),
    ]

    # 构建 vLLM 聊天模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        logger.debug(f"Executing request with vLLM model: {self.model_name}")
        parameters = {
            "api_key": SecretStr(self.api_key).get_secret_value() if self.api_key else None,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens or None,
            "model_kwargs": self.model_kwargs or {},
            "base_url": self.api_base or "http://localhost:8000/v1",
            "temperature": self.temperature if self.temperature is not None else 0.1,
        }

        # Only add optional parameters if explicitly set (not -1)
        # 仅在显式设置时添加可选参数（值不为 -1 时）
        if self.seed is not None and self.seed != -1:
            parameters["seed"] = self.seed
        if self.timeout is not None and self.timeout != -1:
            parameters["timeout"] = self.timeout
        if self.max_retries is not None and self.max_retries != -1:
            parameters["max_retries"] = self.max_retries

        output = ChatOpenAI(**parameters)
        if self.json_mode:
            output = output.bind(response_format={"type": "json_object"})

        return output

    def _get_exception_message(self, e: Exception):
        """从 vLLM 异常中提取错误消息。

        Get a message from a vLLM exception.

        Args:
            e (Exception): The exception to get the message from.

        Returns:
            str: The message from the exception.
        """
        try:
            from openai import BadRequestError
        except ImportError:
            return None
        if isinstance(e, BadRequestError):
            message = e.body.get("message")
            if message:
                return message
        return None

    # 更新构建配置（vLLM 模型支持所有参数，无需特殊处理）
    def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:  # noqa: ARG002
        # vLLM models support all parameters, so no special handling needed
        return build_config
