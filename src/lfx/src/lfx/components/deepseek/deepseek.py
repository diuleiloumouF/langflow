# HTTP 请求库
import requests

# Pydantic v1 的 SecretStr 用于安全存储 API 密钥
from pydantic.v1 import SecretStr

# 方法重写装饰器
from typing_extensions import override

# 模型组件基类
from lfx.base.models.model import LCModelComponent

# 语言模型类型
from lfx.field_typing import LanguageModel

# 范围规范，用于定义滑块输入的范围
from lfx.field_typing.range_spec import RangeSpec

# 输入组件类型
from lfx.inputs.inputs import BoolInput, DictInput, DropdownInput, IntInput, SecretStrInput, SliderInput, StrInput

# DeepSeek 支持的模型列表
DEEPSEEK_MODELS = ["deepseek-chat"]


# DeepSeek 语言模型组件，用于文本生成
class DeepSeekModelComponent(LCModelComponent):
    display_name = "DeepSeek"
    description = "Generate text using DeepSeek LLMs."
    icon = "DeepSeek"

    # 输入参数定义
    inputs = [
        # 继承父类的基础输入参数
        *LCModelComponent.get_base_inputs(),
        # 最大生成 token 数量，0 表示无限制
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            info="Maximum number of tokens to generate. Set to 0 for unlimited.",
            range_spec=RangeSpec(min=0, max=128000),
        ),
        # 模型额外的关键词参数
        DictInput(
            name="model_kwargs",
            display_name="Model Kwargs",
            advanced=True,
            info="Additional keyword arguments to pass to the model.",
        ),
        # JSON 模式：强制输出 JSON 格式
        BoolInput(
            name="json_mode",
            display_name="JSON Mode",
            advanced=True,
            info="If True, it will output JSON regardless of passing a schema.",
        ),
        # 模型名称选择（支持下拉选择和刷新）
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            info="DeepSeek model to use",
            options=DEEPSEEK_MODELS,
            value="deepseek-chat",
            refresh_button=True,
        ),
        # API 基础 URL
        StrInput(
            name="api_base",
            display_name="DeepSeek API Base",
            advanced=True,
            info="Base URL for API requests. Defaults to https://api.deepseek.com",
            value="https://api.deepseek.com",
        ),
        # DeepSeek API 密钥
        SecretStrInput(
            name="api_key",
            display_name="DeepSeek API Key",
            info="The DeepSeek API Key",
            advanced=False,
            required=True,
        ),
        # 温度参数：控制生成文本的随机性
        SliderInput(
            name="temperature",
            display_name="Temperature",
            info="Controls randomness in responses",
            value=1.0,
            range_spec=RangeSpec(min=0, max=2, step=0.01),
            advanced=True,
        ),
        # 随机种子：控制生成结果的可复现性
        IntInput(
            name="seed",
            display_name="Seed",
            info="The seed controls the reproducibility of the job.",
            advanced=True,
            value=1,
        ),
    ]

    # 从 DeepSeek API 获取可用模型列表
    def get_models(self) -> list[str]:
        if not self.api_key:
            return DEEPSEEK_MODELS

        url = f"{self.api_base}/models"
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            model_list = response.json()
            return [model["id"] for model in model_list.get("data", [])]
        except requests.RequestException as e:
            self.status = f"Error fetching models: {e}"
            return DEEPSEEK_MODELS

    # 动态更新构建配置，当 API 密钥、基础 URL 或模型名称变更时刷新模型选项
    @override
    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        if field_name in {"api_key", "api_base", "model_name"}:
            models = self.get_models()
            build_config["model_name"]["options"] = models
        return build_config

    # 构建 DeepSeek 语言模型实例（基于 OpenAI 兼容接口）
    def build_model(self) -> LanguageModel:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            msg = "langchain-openai not installed. Please install with `pip install langchain-openai`"
            raise ImportError(msg) from e

        # 将 API 密钥转换为 SecretStr 格式
        api_key = SecretStr(self.api_key).get_secret_value() if self.api_key else None
        output = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature if self.temperature is not None else 0.1,
            max_tokens=self.max_tokens or None,
            model_kwargs=self.model_kwargs or {},
            base_url=self.api_base,
            api_key=api_key,
            streaming=self.stream if hasattr(self, "stream") else False,
            seed=self.seed,
        )

        # 如果启用了 JSON 模式，绑定 JSON 响应格式
        if self.json_mode:
            output = output.bind(response_format={"type": "json_object"})

        return output

    # 从 DeepSeek API 异常中提取错误消息
    def _get_exception_message(self, e: Exception):
        """Get message from DeepSeek API exception."""
        try:
            from openai import BadRequestError

            if isinstance(e, BadRequestError):
                message = e.body.get("message")
                if message:
                    return message
        except ImportError:
            pass
        return None
