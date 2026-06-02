import httpx
from langchain_openai import ChatOpenAI
from pydantic.v1 import SecretStr

from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import IntInput, SecretStrInput, SliderInput, StrInput


class LiteLLMProxyComponent(LCModelComponent):
    """LiteLLM Proxy component for routing to multiple LLM providers."""

    # 显示名称，用于在画布上展示
    display_name = "LiteLLM Proxy"
    # 组件描述信息
    description = "Generate text using any LLM provider via a LiteLLM proxy with virtual key authentication."
    # 组件图标标识
    icon = "LiteLLM"
    # 组件内部名称，用于流程 JSON 中标识
    name = "LiteLLMProxyModel"

    # 组件输入参数定义列表
    inputs = [
        # 继承基础模型组件的所有输入参数（如 stream、input_value 等）
        *LCModelComponent.get_base_inputs(),
        # LiteLLM 代理服务的 API 地址
        StrInput(
            name="api_base",
            display_name="LiteLLM Proxy URL",
            value="http://localhost:4000/v1",
            required=True,
            info="Base URL of the LiteLLM proxy.",
        ),
        # 虚拟密钥，用于认证
        SecretStrInput(
            name="api_key",
            display_name="Virtual Key",
            value="LITELLM_API_KEY",
            required=True,
            info="Virtual key for authentication.",
        ),
        # 要使用的模型名称（如 gpt-4o、claude-3-opus）
        StrInput(
            name="model_name",
            display_name="Model Name",
            required=True,
            info="Model name to use (e.g. gpt-4o, claude-3-opus).",
        ),
        # 温度参数，控制生成文本的随机性，值越低越确定性
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.7,
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            advanced=True,
            info="Controls randomness. Lower values are more deterministic.",
        ),
        # 最大 token 数限制，设为 0 表示不限制
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            info="Maximum number of tokens to generate. Set to 0 for no limit.",
            range_spec=RangeSpec(min=0, max=128000),
        ),
        # 请求超时时间（秒）
        IntInput(
            name="timeout",
            display_name="Timeout (seconds)",
            value=60,
            advanced=True,
            info="Request timeout in seconds.",
        ),
        # 失败时的最大重试次数
        IntInput(
            name="max_retries",
            display_name="Max Retries",
            value=2,
            advanced=True,
            info="Maximum number of retries on failure.",
        ),
    ]

    def build_model(self) -> LanguageModel:
        """Build the LiteLLM proxy model."""
        # 获取 API 密钥，如果是 SecretStr 类型则提取实际值
        api_key = self.api_key
        if isinstance(api_key, SecretStr):
            api_key = api_key.get_secret_value()

        # 验证代理服务连接是否正常
        self._validate_proxy_connection(api_key)

        # 使用 LangChain 的 ChatOpenAI 客户端连接 LiteLLM 代理
        # LiteLLM 代理兼容 OpenAI API 格式，因此可直接使用 ChatOpenAI
        return ChatOpenAI(
            base_url=self.api_base,
            api_key=api_key,
            model=self.model_name,
            temperature=self.temperature,
            # max_tokens 为 0 时传 None 表示不限制
            max_tokens=self.max_tokens if self.max_tokens != 0 else None,
            timeout=self.timeout,
            max_retries=self.max_retries,
            streaming=self.stream,
        )

    def _validate_proxy_connection(self, api_key: str) -> None:
        """Validate the proxy connection, API key, and model availability."""
        # 去除末尾斜杠，拼接 /models 端点地址
        base_url = self.api_base.rstrip("/")
        models_url = f"{base_url}/models"

        try:
            # 向代理服务发送请求，获取可用模型列表
            response = httpx.get(
                models_url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
        except httpx.ConnectError as e:
            # 连接失败：代理服务未启动或地址错误
            msg = (
                f"Could not connect to LiteLLM Proxy at {base_url}. Verify the URL is correct and the proxy is running."
            )
            raise ValueError(msg) from e
        except httpx.TimeoutException as e:
            # 连接超时
            msg = f"Connection to LiteLLM Proxy at {base_url} timed out."
            raise ValueError(msg) from e

        # HTTP 401 未授权：API 密钥无效或已过期
        http_unauthorized = 401
        if response.status_code == http_unauthorized:
            msg = "Authentication failed. Check that your Virtual Key is valid and not expired."
            raise ValueError(msg)

        # 其他 HTTP 错误直接抛出
        response.raise_for_status()

        # 检查用户指定的模型是否在代理服务的可用模型列表中
        data = response.json()
        available_models = [m.get("id", "") for m in data.get("data", [])]
        if available_models and self.model_name not in available_models:
            msg = (
                f"Model '{self.model_name}' not found on the LiteLLM Proxy. "
                f"Available models: {', '.join(available_models)}"
            )
            raise ValueError(msg)

    def _get_exception_message(self, e: Exception) -> str | None:
        """Extract meaningful error messages from OpenAI client exceptions."""
        try:
            # 尝试导入 OpenAI 客户端的异常类型
            from openai import AuthenticationError, BadRequestError, NotFoundError
        except ImportError:
            # 未安装 openai 包则无法提取详细错误信息
            return None

        # 认证失败：密钥无效或已过期
        if isinstance(e, AuthenticationError):
            return "Authentication failed. Check that your Virtual Key is valid and not expired."
        # 模型未找到
        if isinstance(e, NotFoundError):
            return f"Model '{self.model_name}' not found. Verify the model name."
        # 请求参数错误，尝试从响应体中提取错误消息
        if isinstance(e, BadRequestError):
            message = e.body.get("message") if isinstance(e.body, dict) else None
            if message:
                return message
        return None
