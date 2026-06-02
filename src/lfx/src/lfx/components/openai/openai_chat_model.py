from typing import Any

from langchain_openai import ChatOpenAI
from pydantic.v1 import SecretStr

from lfx.base.models.model import LCModelComponent
from lfx.base.models.openai_constants import OPENAI_CHAT_MODEL_NAMES, OPENAI_REASONING_MODEL_NAMES
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import BoolInput, DictInput, DropdownInput, IntInput, SecretStrInput, SliderInput, StrInput
from lfx.log.logger import logger


# OpenAI 聊天模型组件，封装了 OpenAI API 的对话模型调用能力
class OpenAIModelComponent(LCModelComponent):
    display_name = "OpenAI"
    description = "Generates text using OpenAI LLMs."
    icon = "OpenAI"
    name = "OpenAIModel"

    # 组件输入参数定义
    inputs = [
        *LCModelComponent.get_base_inputs(),
        # max_tokens: 生成的最大 token 数量，设为 0 表示无限制
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            info="The maximum number of tokens to generate. Set to 0 for unlimited tokens.",
            range_spec=RangeSpec(min=0, max=128000),
        ),
        # model_kwargs: 传递给模型的额外关键字参数
        DictInput(
            name="model_kwargs",
            display_name="Model Kwargs",
            advanced=True,
            info="Additional keyword arguments to pass to the model.",
        ),
        # json_mode: 是否启用 JSON 输出模式，强制模型返回 JSON 格式
        BoolInput(
            name="json_mode",
            display_name="JSON Mode",
            advanced=True,
            info="If True, it will output JSON regardless of passing a schema.",
        ),
        # model_name: 模型名称下拉选择框，包含聊天模型和推理模型
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            advanced=False,
            options=OPENAI_CHAT_MODEL_NAMES + OPENAI_REASONING_MODEL_NAMES,
            value=OPENAI_CHAT_MODEL_NAMES[0],
            combobox=True,
            real_time_refresh=True,
        ),
        # openai_api_base: OpenAI API 基础 URL，可切换至其他兼容 API 服务
        StrInput(
            name="openai_api_base",
            display_name="OpenAI API Base",
            advanced=True,
            info="The base URL of the OpenAI API. "
            "Defaults to https://api.openai.com/v1. "
            "You can change this to use other APIs like JinaChat, LocalAI and Prem.",
        ),
        # api_key: OpenAI API 密钥，用于身份认证
        SecretStrInput(
            name="api_key",
            display_name="OpenAI API Key",
            info="The OpenAI API Key to use for the OpenAI model.",
            advanced=False,
            value="OPENAI_API_KEY",
            required=True,
        ),
        # temperature: 温度参数，控制生成文本的随机性，范围 0~1
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            show=True,
        ),
        # seed: 随机种子，用于控制生成结果的可复现性
        IntInput(
            name="seed",
            display_name="Seed",
            info="The seed controls the reproducibility of the job.",
            advanced=True,
            value=1,
        ),
        # max_retries: 请求失败时的最大重试次数
        IntInput(
            name="max_retries",
            display_name="Max Retries",
            info="The maximum number of retries to make when generating.",
            advanced=True,
            value=5,
        ),
        # timeout: 请求超时时间（秒）
        IntInput(
            name="timeout",
            display_name="Timeout",
            info="The timeout for requests to OpenAI completion API.",
            advanced=True,
            value=700,
        ),
    ]

    # 构建并返回 LangChain 的 ChatOpenAI 模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        logger.debug(f"Executing request with model: {self.model_name}")
        # 处理 api_key —— 它可能是字符串或 SecretStr 类型
        api_key_value = None
        if self.api_key:
            logger.debug(f"API key type: {type(self.api_key)}, value: {'***' if self.api_key else None}")
            if isinstance(self.api_key, SecretStr):
                api_key_value = self.api_key.get_secret_value()
            else:
                api_key_value = str(self.api_key)
        logger.debug(f"Final api_key_value type: {type(api_key_value)}, value: {'***' if api_key_value else None}")

        # 处理 model_kwargs，确保其中不包含 api_key 以避免冲突
        model_kwargs = self.model_kwargs or {}
        # 从 model_kwargs 中移除 api_key（如果存在），防止参数冲突
        if "api_key" in model_kwargs:
            logger.warning("api_key found in model_kwargs, removing to prevent conflicts")
            model_kwargs = dict(model_kwargs)  # 创建副本避免修改原始数据
            del model_kwargs["api_key"]

        # 组装模型初始化参数
        parameters = {
            "api_key": api_key_value,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens or None,
            "model_kwargs": model_kwargs,
            "base_url": self.openai_api_base or "https://api.openai.com/v1",
            "max_retries": self.max_retries,
            "timeout": self.timeout,
        }

        # TODO: Revisit if/once parameters are supported for reasoning models
        # 推理模型不支持的参数列表
        unsupported_params_for_reasoning_models = ["temperature", "seed"]

        # 非推理模型支持 temperature 和 seed 参数
        if self.model_name not in OPENAI_REASONING_MODEL_NAMES:
            parameters["temperature"] = self.temperature if self.temperature is not None else 0.1
            parameters["seed"] = self.seed
        else:
            params_str = ", ".join(unsupported_params_for_reasoning_models)
            logger.debug(f"{self.model_name} is a reasoning model, {params_str} are not configurable. Ignoring.")

        # 确保所有参数值类型正确
        if isinstance(parameters.get("api_key"), SecretStr):
            parameters["api_key"] = parameters["api_key"].get_secret_value()
        parameters["stream_usage"] = True
        # 创建 ChatOpenAI 实例
        output = ChatOpenAI(**parameters)
        # 如果启用了 JSON 模式，绑定 JSON 响应格式
        if self.json_mode:
            output = output.bind(response_format={"type": "json_object"})

        return output

    # 从 OpenAI 异常中提取用户可读的错误信息
    def _get_exception_message(self, e: Exception):
        """Get a message from an OpenAI exception.

        Args:
            e (Exception): The exception to get the message from.

        Returns:
            str: The message from the exception.
        """
        try:
            from openai import BadRequestError, NotFoundError
        except ImportError:
            return None
        # 处理模型不存在的情况，提示用户检查账户权限或更换模型
        if isinstance(e, NotFoundError):
            body = getattr(e, "body", None) or {}
            if isinstance(body, dict) and body.get("code") == "model_not_found":
                return (
                    f"Model '{self.model_name}' is not available for this OpenAI account. "
                    "Your API tier may not have access yet — check "
                    "https://platform.openai.com/settings/organization/limits "
                    "or select a different model."
                )
        # 处理请求参数错误，返回 API 返回的具体错误信息
        if isinstance(e, BadRequestError):
            message = e.body.get("message")
            if message:
                return message
        return None

    # 根据当前选中的模型动态更新构建配置（显示/隐藏相关参数）
    def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        # 选择推理模型时，隐藏 temperature 和 seed（不支持的参数）
        if field_name in {"base_url", "model_name", "api_key"} and field_value in OPENAI_REASONING_MODEL_NAMES:
            build_config["temperature"]["show"] = False
            build_config["seed"]["show"] = False
            # Hide system_message for o1 models - currently unsupported
            # o1 系列模型当前不支持 system_message，一并隐藏
            if field_value.startswith("o1") and "system_message" in build_config:
                build_config["system_message"]["show"] = False
        # 选择聊天模型时，显示 temperature、seed 和 system_message
        if field_name in {"base_url", "model_name", "api_key"} and field_value in OPENAI_CHAT_MODEL_NAMES:
            build_config["temperature"]["show"] = True
            build_config["seed"]["show"] = True
            if "system_message" in build_config:
                build_config["system_message"]["show"] = True
        return build_config
