# 类型标注导入
from typing import Any

# LangChain 模型基类
from lfx.base.models.model import LCModelComponent

# 语言模型类型定义
from lfx.field_typing import LanguageModel

# 范围规范类型，用于定义滑块输入的范围
from lfx.field_typing.range_spec import RangeSpec

# 各种输入组件类型
from lfx.inputs.inputs import BoolInput, DropdownInput, IntInput, MessageTextInput, SecretStrInput, SliderInput

# 点字典类型，用于灵活访问配置字典
from lfx.schema.dotdict import dotdict


# NVIDIA LLM 模型组件，用于调用 NVIDIA 提供的大语言模型生成文本
class NVIDIAModelComponent(LCModelComponent):
    # 组件显示名称
    display_name = "NVIDIA"
    # 组件描述信息
    description = "Generates text using NVIDIA LLMs."
    # 组件图标
    icon = "NVIDIA"

    # 组件输入参数列表
    inputs = [
        # 继承基础模型组件的所有输入参数
        *LCModelComponent.get_base_inputs(),
        # 最大生成令牌数，设为 0 表示无限制
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            info="The maximum number to tokens to generate. Set to 0 for unlimited tokens.",
        ),
        # 模型名称下拉选择框，支持动态刷新
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            info="The name of the NVIDIA model to use.",
            advanced=False,
            value=None,
            options=[],
            combobox=True,
            refresh_button=True,
        ),
        # 详细思考模式开关，仅推理模型支持
        BoolInput(
            name="detailed_thinking",
            display_name="Detailed Thinking",
            info="If true, the model will return a detailed thought process. Only supported by reasoning models.",
            value=False,
            show=False,
        ),
        # 工具模型启用开关，启用后仅显示支持工具调用的模型
        BoolInput(
            name="tool_model_enabled",
            display_name="Enable Tool Models",
            info="If enabled, only show models that support tool-calling.",
            advanced=False,
            value=False,
            real_time_refresh=True,
        ),
        # NVIDIA API 基础 URL
        MessageTextInput(
            name="base_url",
            display_name="NVIDIA Base URL",
            value="https://integrate.api.nvidia.com/v1",
            info="The base URL of the NVIDIA API. Defaults to https://integrate.api.nvidia.com/v1.",
        ),
        # NVIDIA API 密钥（安全字符串）
        SecretStrInput(
            name="api_key",
            display_name="NVIDIA API Key",
            info="The NVIDIA API Key.",
            advanced=False,
            value="NVIDIA_API_KEY",
        ),
        # 温度参数，控制生成文本的随机性（0-1）
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            info="Run inference with this temperature.",
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            advanced=True,
        ),
        # 随机种子，用于保证生成结果的可重复性
        IntInput(
            name="seed",
            display_name="Seed",
            info="The seed controls the reproducibility of the job.",
            advanced=True,
            value=1,
        ),
    ]

    # 获取可用的 NVIDIA 模型列表
    def get_models(self, *, tool_model_enabled: bool | None = None) -> list[str]:
        try:
            from langchain_nvidia_ai_endpoints import ChatNVIDIA
        except ImportError as e:
            msg = "Please install langchain-nvidia-ai-endpoints to use the NVIDIA model."
            raise ImportError(msg) from e

        # Note: don't include the previous model, as it may not exist in available models from the new base url
        # 创建 NVIDIA 模型实例
        model = ChatNVIDIA(base_url=self.base_url, api_key=self.api_key)
        # 如果启用了工具模型筛选，仅返回支持工具调用的模型
        if tool_model_enabled:
            tool_models = [m for m in model.get_available_models() if m.supports_tools]
            return sorted(m.id for m in tool_models)
        # 返回所有可用模型的排序列表
        return sorted(m.id for m in model.available_models)

    # 更新构建配置，当相关字段变化时刷新模型列表
    def update_build_config(self, build_config: dotdict, _field_value: Any, field_name: str | None = None):
        # 当模型名称、工具模型开关、基础 URL 或 API 密钥变化时更新配置
        if field_name in {"model_name", "tool_model_enabled", "base_url", "api_key"}:
            try:
                # 获取可用模型列表
                ids = self.get_models(tool_model_enabled=self.tool_model_enabled)
                build_config["model_name"]["options"] = ids

                # 设置默认选中的模型
                if "value" not in build_config["model_name"] or build_config["model_name"]["value"] is None:
                    build_config["model_name"]["value"] = ids[0]
                elif build_config["model_name"]["value"] not in ids:
                    build_config["model_name"]["value"] = None

                # TODO: use api to determine if model supports detailed thinking
                # Nemotron 模型支持详细思考模式
                if build_config["model_name"]["value"] == "nemotron":
                    build_config["detailed_thinking"]["show"] = True
                else:
                    build_config["detailed_thinking"]["value"] = False
                    build_config["detailed_thinking"]["show"] = False
            except Exception as e:
                msg = f"Error getting model names: {e}"
                build_config["model_name"]["value"] = None
                build_config["model_name"]["options"] = []
                raise ValueError(msg) from e

        return build_config

    # 构建并返回配置好的 NVIDIA 模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        try:
            from langchain_nvidia_ai_endpoints import ChatNVIDIA
        except ImportError as e:
            msg = "Please install langchain-nvidia-ai-endpoints to use the NVIDIA model."
            raise ImportError(msg) from e
        # 获取组件配置参数
        api_key = self.api_key
        temperature = self.temperature
        model_name: str = self.model_name
        max_tokens = self.max_tokens
        seed = self.seed
        # 创建并返回配置好的 ChatNVIDIA 模型实例
        return ChatNVIDIA(
            max_tokens=max_tokens or None,
            model=model_name,
            base_url=self.base_url,
            api_key=api_key,
            temperature=temperature or 0.1,
            seed=seed,
        )
