from typing import Any

import requests
from pydantic.v1 import SecretStr

# Google Generative AI 模型常量列表
from lfx.base.models.google_generative_ai_constants import GOOGLE_GENERATIVE_AI_MODELS

# 修复后的 ChatGoogleGenerativeAI 模型类，支持多函数调用
from lfx.base.models.google_generative_ai_model import ChatGoogleGenerativeAIFixed

# 语言模型组件基类
from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import BoolInput, DropdownInput, FloatInput, IntInput, SecretStrInput, SliderInput
from lfx.log.logger import logger
from lfx.schema.dotdict import dotdict


# Google Generative AI 语言模型组件
# 提供 Google Gemini 系列模型的接入能力，支持文本生成、流式输出、函数调用等功能
class GoogleGenerativeAIComponent(LCModelComponent):
    display_name = "Google Generative AI"
    description = "Generate text using Google Generative AI."
    icon = "GoogleGenerativeAI"
    name = "GoogleGenerativeAIModel"

    # 组件输入参数定义
    inputs = [
        *LCModelComponent.get_base_inputs(),
        # 最大输出 token 数
        IntInput(
            name="max_output_tokens", display_name="Max Output Tokens", info="The maximum number of tokens to generate."
        ),
        # 模型选择下拉框，支持动态刷新和自定义输入
        DropdownInput(
            name="model_name",
            display_name="Model",
            info="The name of the model to use.",
            options=GOOGLE_GENERATIVE_AI_MODELS,
            value="gemini-2.5-flash",
            refresh_button=True,
            combobox=True,
        ),
        # Google API 密钥，变更时实时刷新模型列表
        SecretStrInput(
            name="api_key",
            display_name="Google API Key",
            info="The Google API Key to use for the Google Generative AI.",
            required=True,
            real_time_refresh=True,
        ),
        # Top-P 采样参数（累积概率截断）
        FloatInput(
            name="top_p",
            display_name="Top P",
            info="The maximum cumulative probability of tokens to consider when sampling.",
            advanced=True,
        ),
        # 温度参数，控制生成随机性（0=确定性高，1=创造性高）
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            info="Controls randomness. Lower values are more deterministic, higher values are more creative.",
        ),
        # 每次请求生成的补全数量
        IntInput(
            name="n",
            display_name="N",
            info="Number of chat completions to generate for each prompt. "
            "Note that the API may not return the full n completions if duplicates are generated.",
            advanced=True,
        ),
        # Top-K 采样参数
        IntInput(
            name="top_k",
            display_name="Top K",
            info="Decode using top-k sampling: consider the set of top_k most probable tokens. Must be positive.",
            advanced=True,
        ),
        # 是否启用工具调用（函数调用）能力
        BoolInput(
            name="tool_model_enabled",
            display_name="Tool Model Enabled",
            info="Whether to use the tool model.",
            value=False,
        ),
    ]

    # 构建并返回 LangChain 语言模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        google_api_key = self.api_key
        model = self.model_name
        max_output_tokens = self.max_output_tokens
        temperature = self.temperature
        top_k = self.top_k
        top_p = self.top_p
        n = self.n

        # Use modified ChatGoogleGenerativeAIFixed class for multiple function support
        # TODO: Potentially remove when fixed upstream
        # 使用修复后的 ChatGoogleGenerativeAIFixed 类，支持多函数调用
        return ChatGoogleGenerativeAIFixed(
            model=model,
            max_output_tokens=max_output_tokens or None,
            temperature=temperature,
            top_k=top_k or None,
            top_p=top_p or None,
            n=n or 1,
            google_api_key=SecretStr(google_api_key).get_secret_value(),
        )

    # 获取可用的模型列表，支持按工具调用能力筛选
    def get_models(self, *, tool_model_enabled: bool | None = None) -> list[str]:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            # 从 Google API 获取所有支持 generateContent 的模型，去除 "models/" 前缀
            model_ids = [
                model.name.replace("models/", "")
                for model in genai.list_models()
                if "generateContent" in model.supported_generation_methods
            ]
            model_ids.sort(reverse=True)
        except (ImportError, ValueError) as e:
            logger.exception(f"Error getting model names: {e}")
            # 获取失败时回退到内置的模型列表
            model_ids = GOOGLE_GENERATIVE_AI_MODELS
        # 如果启用了工具模型筛选，移除不支持函数调用的模型
        if tool_model_enabled:
            try:
                from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
            except ImportError as e:
                msg = "langchain_google_genai is not installed."
                raise ImportError(msg) from e
            for model in model_ids:
                model_with_tool = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                )
                if not self.supports_tool_calling(model_with_tool):
                    model_ids.remove(model)
        return model_ids

    # 当用户修改关键字段时，动态更新模型下拉列表的选项
    def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        # 仅在修改 API 密钥、模型名称、基础 URL 或工具模型开关时触发更新
        if field_name in {"base_url", "model_name", "tool_model_enabled", "api_key"} and field_value:
            try:
                if len(self.api_key) == 0:
                    # API 密钥为空时使用内置模型列表
                    ids = GOOGLE_GENERATIVE_AI_MODELS
                else:
                    try:
                        # 尝试从 Google API 动态获取模型列表
                        ids = self.get_models(tool_model_enabled=self.tool_model_enabled)
                    except (ImportError, ValueError, requests.exceptions.RequestException) as e:
                        logger.exception(f"Error getting model names: {e}")
                        ids = GOOGLE_GENERATIVE_AI_MODELS
                build_config.setdefault("model_name", {})
                # 更新模型下拉选项
                build_config["model_name"]["options"] = ids
                build_config["model_name"].setdefault("value", ids[0])
            except Exception as e:
                msg = f"Error getting model names: {e}"
                raise ValueError(msg) from e
        return build_config
