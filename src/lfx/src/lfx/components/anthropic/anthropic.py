from typing import Any, cast

import requests
from pydantic import ValidationError

# Anthropic 模型相关常量
from lfx.base.models.anthropic_constants import (
    ANTHROPIC_MODELS,
    DEFAULT_ANTHROPIC_API_URL,
    TOOL_CALLING_SUPPORTED_ANTHROPIC_MODELS,
    TOOL_CALLING_UNSUPPORTED_ANTHROPIC_MODELS,
)

# 语言模型基类
from lfx.base.models.model import LCModelComponent

# 语言模型类型
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec

# 输入组件类型
from lfx.io import BoolInput, DropdownInput, IntInput, MessageTextInput, SecretStrInput, SliderInput

# 日志记录器
from lfx.log.logger import logger

# 点字典类型，支持点号访问
from lfx.schema.dotdict import dotdict


class AnthropicModelComponent(LCModelComponent):
    """Anthropic 模型组件，通过 Anthropic Messages API 生成文本。

    支持多种 Claude 模型，包括支持工具调用的模型和不支持工具调用的模型。
    可以配置 API 密钥、模型名称、温度、最大令牌数等参数。
    """

    display_name = "Anthropic"
    # 组件显示名称
    description = "Generate text using Anthropic's Messages API and models."
    # 组件描述
    icon = "Anthropic"
    # 组件图标
    name = "AnthropicModel"
    # 组件内部名称

    inputs = [
        *LCModelComponent.get_base_inputs(),
        # 最大令牌数输入，控制生成文本的最大长度
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            value=4096,
            info="The maximum number of tokens to generate. Set to 0 for unlimited tokens.",
        ),
        # 模型名称下拉选择框，支持手动输入
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            options=ANTHROPIC_MODELS,
            refresh_button=True,
            value=ANTHROPIC_MODELS[0],
            combobox=True,
        ),
        # Anthropic API 密钥输入
        SecretStrInput(
            name="api_key",
            display_name="Anthropic API Key",
            info="Your Anthropic API key.",
            value=None,
            required=True,
            real_time_refresh=True,
        ),
        # 温度滑块，控制生成文本的随机性
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            info="Run inference with this temperature. Must by in the closed interval [0.0, 1.0].",
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            advanced=True,
        ),
        # Anthropic API 端点 URL
        MessageTextInput(
            name="base_url",
            display_name="Anthropic API URL",
            info="Endpoint of the Anthropic API. Defaults to 'https://api.anthropic.com' if not specified.",
            value=DEFAULT_ANTHROPIC_API_URL,
            real_time_refresh=True,
            advanced=True,
        ),
        # 是否启用工具模型开关
        BoolInput(
            name="tool_model_enabled",
            display_name="Enable Tool Models",
            info=(
                "Select if you want to use models that can work with tools. If yes, only those models will be shown."
            ),
            advanced=False,
            value=False,
            real_time_refresh=True,
        ),
    ]

    # 构建 Anthropic 模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        # 导入 langchain_anthropic 聊天模型
        try:
            from langchain_anthropic.chat_models import ChatAnthropic
        except ImportError as e:
            msg = "langchain_anthropic is not installed. Please install it with `pip install langchain_anthropic`."
            raise ImportError(msg) from e
        try:
            # 获取最大令牌数，默认为 4096
            max_tokens_value = getattr(self, "max_tokens", "")
            max_tokens_value = 4096 if max_tokens_value == "" else int(max_tokens_value)
            # 创建 ChatAnthropic 实例
            output = ChatAnthropic(
                model=self.model_name,
                anthropic_api_key=self.api_key,
                max_tokens=max_tokens_value,
                temperature=self.temperature,
                anthropic_api_url=self.base_url or DEFAULT_ANTHROPIC_API_URL,
                streaming=self.stream,
                stream_usage=True,
            )
        except ValidationError:
            raise
        except Exception as e:
            msg = "Could not connect to Anthropic API."
            raise ValueError(msg) from e

        return output

    # 获取可用的模型列表
    def get_models(self, *, tool_model_enabled: bool | None = None) -> list[str]:
        # 尝试从 Anthropic API 获取最新模型列表
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)
            models = client.models.list(limit=20).data
            # 合并预定义模型和 API 返回的模型
            model_ids = ANTHROPIC_MODELS + [model.id for model in models]
        except (ImportError, ValueError, requests.exceptions.RequestException) as e:
            logger.exception(f"Error getting model names: {e}")
            # 如果 API 调用失败，使用预定义模型列表
            model_ids = ANTHROPIC_MODELS

        # 如果启用了工具模型过滤，只返回支持工具调用的模型
        if tool_model_enabled:
            try:
                from langchain_anthropic.chat_models import ChatAnthropic
            except ImportError as e:
                msg = "langchain_anthropic is not installed. Please install it with `pip install langchain_anthropic`."
                raise ImportError(msg) from e

            # Create a new list instead of modifying while iterating
            # 过滤出支持工具调用的模型
            filtered_models = []
            for model in model_ids:
                # 如果模型在已知支持工具调用的列表中，直接添加
                if model in TOOL_CALLING_SUPPORTED_ANTHROPIC_MODELS:
                    filtered_models.append(model)
                    continue

                # 创建模型实例并检查是否支持工具调用
                model_with_tool = ChatAnthropic(
                    model=model,  # Use the current model being checked
                    anthropic_api_key=self.api_key,
                    anthropic_api_url=cast("str", self.base_url) or DEFAULT_ANTHROPIC_API_URL,
                )

                # 如果模型不支持工具调用或在已知不支持列表中，跳过
                if (
                    not self.supports_tool_calling(model_with_tool)
                    or model in TOOL_CALLING_UNSUPPORTED_ANTHROPIC_MODELS
                ):
                    continue

                filtered_models.append(model)

            return filtered_models

        return model_ids

    # 从 Anthropic 异常中提取错误消息
    def _get_exception_message(self, exception: Exception) -> str | None:
        """Get a message from an Anthropic exception.

        Args:
            exception (Exception): The exception to get the message from.

        Returns:
            str: The message from the exception.
        """
        # 尝试导入 Anthropic 的 BadRequestError 异常类
        try:
            from anthropic import BadRequestError
        except ImportError:
            return None
        # 如果是 BadRequestError，提取错误消息
        if isinstance(exception, BadRequestError):
            message = exception.body.get("error", {}).get("message")
            if message:
                return message
        return None

    # 更新构建配置，当相关字段值改变时刷新模型列表
    def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        # 如果 base_url 为空，设置默认值
        if "base_url" in build_config and build_config["base_url"]["value"] is None:
            build_config["base_url"]["value"] = DEFAULT_ANTHROPIC_API_URL
            self.base_url = DEFAULT_ANTHROPIC_API_URL
        # 当 API 密钥、基础 URL、模型名称或工具模型开关改变时，更新模型列表
        if field_name in {"base_url", "model_name", "tool_model_enabled", "api_key"} and field_value:
            try:
                # 如果 API 密钥为空，使用预定义模型列表
                if len(self.api_key) == 0:
                    ids = ANTHROPIC_MODELS
                else:
                    # 尝试从 API 获取最新模型列表
                    try:
                        ids = self.get_models(tool_model_enabled=self.tool_model_enabled)
                    except (ImportError, ValueError, requests.exceptions.RequestException) as e:
                        logger.exception(f"Error getting model names: {e}")
                        ids = ANTHROPIC_MODELS
                # 更新模型下拉框配置
                build_config.setdefault("model_name", {})
                build_config["model_name"]["options"] = ids
                build_config["model_name"].setdefault("value", ids[0])
                build_config["model_name"]["combobox"] = True
            except Exception as e:
                msg = f"Error getting model names: {e}"
                raise ValueError(msg) from e
        return build_config
