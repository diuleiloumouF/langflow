# 引入密钥处理类
from pydantic.v1 import SecretStr

# 引入 Groq 模型常量和动态发现模块
from lfx.base.models.groq_constants import GROQ_MODELS
from lfx.base.models.groq_model_discovery import get_groq_models

# 引入语言模型组件基类
from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec

# 引入各类输入组件类型
from lfx.io import BoolInput, DropdownInput, IntInput, MessageTextInput, SecretStrInput, SliderInput

# 引入日志记录器
from lfx.log.logger import logger


class GroqModel(LCModelComponent):
    """Groq 语言模型组件，使用 Groq API 生成文本。"""

    # 组件在界面上的显示名称
    display_name: str = "Groq"
    # 组件的功能描述
    description: str = "Generate text using Groq."
    # 组件图标
    icon = "Groq"
    # 组件内部名称
    name = "GroqModel"

    # 组件输入参数定义
    inputs = [
        *LCModelComponent.get_base_inputs(),
        SecretStrInput(
            name="api_key", display_name="Groq API Key", info="API key for the Groq API.", real_time_refresh=True
        ),
        MessageTextInput(
            name="base_url",
            display_name="Groq API Base",
            info="Base URL path for API requests, leave blank if not using a proxy or service emulator.",
            advanced=True,
            value="https://api.groq.com",
            real_time_refresh=True,
        ),
        IntInput(
            name="max_tokens",
            display_name="Max Output Tokens",
            info="The maximum number of tokens to generate.",
            advanced=True,
        ),
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            info="Run inference with this temperature. Must by in the closed interval [0.0, 1.0].",
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            advanced=True,
        ),
        IntInput(
            name="n",
            display_name="N",
            info="Number of chat completions to generate for each prompt. "
            "Note that the API may not return the full n completions if duplicates are generated.",
            advanced=True,
        ),
        DropdownInput(
            name="model_name",
            display_name="Model",
            info="The name of the model to use. Add your Groq API key to access additional available models.",
            options=GROQ_MODELS,
            value=GROQ_MODELS[0],
            refresh_button=True,
            combobox=True,
        ),
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

    def get_models(self, *, tool_model_enabled: bool | None = None) -> list[str]:
        """使用动态发现系统获取可用的 Groq 模型列表。

        此方法使用 groq_model_discovery 模块，该模块会：
        - 直接从 Groq API 获取模型列表
        - 自动测试工具调用支持
        - 缓存结果 24 小时
        - 如果 API 失败则回退到硬编码列表

        Args:
            tool_model_enabled: 如果为 True，则仅返回支持工具调用的模型

        Returns:
            可用模型 ID 的列表
        """
        try:
            # 从动态发现系统获取模型及其元数据
            # Get models with metadata from dynamic discovery system
            api_key = self.api_key if hasattr(self, "api_key") and self.api_key else None
            models_metadata = get_groq_models(api_key=api_key)

            # 过滤掉非 LLM 模型（音频、TTS、守护模型等）
            # Filter out non-LLM models (audio, TTS, guards)
            model_ids = [
                model_id for model_id, metadata in models_metadata.items() if not metadata.get("not_supported", False)
            ]

            # 如果请求，按工具调用支持进行过滤
            # Filter by tool calling support if requested
            if tool_model_enabled:
                model_ids = [model_id for model_id in model_ids if models_metadata[model_id].get("tool_calling", False)]
                logger.info(f"Loaded {len(model_ids)} Groq models with tool calling support")
            else:
                logger.info(f"Loaded {len(model_ids)} Groq models")
        except (ValueError, KeyError, TypeError, ImportError):
            logger.exception("Error getting model names")
            # 如果获取失败，回退到 groq_constants.py 中的硬编码列表
            # Fallback to hardcoded list from groq_constants.py
            return GROQ_MODELS
        else:
            return model_ids

    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        if field_name in {"base_url", "model_name", "tool_model_enabled", "api_key"} and field_value:
            try:
                if len(self.api_key) != 0:
                    try:
                        ids = self.get_models(tool_model_enabled=self.tool_model_enabled)
                    except (ValueError, KeyError, TypeError, ImportError):
                        logger.exception("Error getting model names")
                        ids = GROQ_MODELS
                    ids = ids or GROQ_MODELS
                    build_config.setdefault("model_name", {})
                    build_config["model_name"]["options"] = ids
                    build_config["model_name"].setdefault("value", ids[0])
            except (ValueError, KeyError, TypeError, AttributeError) as e:
                msg = f"Error getting model names: {e}"
                raise ValueError(msg) from e
        return build_config

    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        """构建并返回 Groq 语言模型实例。"""
        try:
            from langchain_groq import ChatGroq
        except ImportError as e:
            msg = "langchain-groq is not installed. Please install it with `pip install langchain-groq`."
            raise ImportError(msg) from e

        return ChatGroq(
            model=self.model_name,
            max_tokens=self.max_tokens or None,
            temperature=self.temperature,
            base_url=self.base_url,
            n=self.n or 1,
            api_key=SecretStr(self.api_key).get_secret_value(),
            streaming=self.stream,
        )
