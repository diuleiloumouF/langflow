"""Factory functions for creating and configuring LLM instances for different providers."""

# LLM 工厂模块：为不同提供商创建和配置 LLM 实例的工厂函数

from __future__ import annotations

from typing import TYPE_CHECKING

# 导入 IBM WatsonX 的 URL 常量
from lfx.base.models.watsonx_constants import IBM_WATSONX_URLS

# 导入各 LLM 提供商的常量定义
from lfx.components.agentics.constants import (
    DEFAULT_OLLAMA_URL,  # Ollama 默认本地地址
    ERROR_UNSUPPORTED_PROVIDER,  # 不支持的提供商错误信息模板
    LLM_MODEL_PREFIXES,  # 各提供商的模型名前缀映射
    PROVIDER_ANTHROPIC,  # Anthropic 提供商标识
    PROVIDER_GOOGLE,  # Google 提供商标识
    PROVIDER_IBM_WATSONX,  # IBM WatsonX 提供商标识
    PROVIDER_OLLAMA,  # Ollama 提供商标识
    PROVIDER_OPENAI,  # OpenAI 提供商标识
    WATSONX_DEFAULT_MAX_INPUT_TOKENS,  # WatsonX 默认最大输入 token 数
    WATSONX_DEFAULT_MAX_TOKENS,  # WatsonX 默认最大输出 token 数
    WATSONX_DEFAULT_TEMPERATURE,  # WatsonX 默认温度参数
)

if TYPE_CHECKING:
    from crewai import LLM


def create_llm(
    provider: str,
    model_name: str,
    api_key: str | None,
    *,
    base_url_ibm_watsonx: str | None = None,
    project_id: str | None = None,
    ollama_base_url: str | None = None,
) -> LLM:
    """Create and configure an LLM instance for the specified provider.

    Args:
        provider: The LLM provider name (e.g., "OpenAI", "Anthropic", "IBM WatsonX").
        model_name: The model identifier without provider prefix.
        api_key: The API key for authentication (not required for Ollama).
        base_url_ibm_watsonx: Base URL for IBM WatsonX API endpoint (WatsonX only).
        project_id: Project ID for IBM WatsonX (WatsonX only).
        ollama_base_url: Base URL for Ollama API endpoint (Ollama only).

    Returns:
        Configured LLM instance ready for use with the Agentics framework.

    Raises:
        ValueError: If the provider is not supported or configuration is invalid.
    """
    # 创建并配置指定提供商的 LLM 实例

    # 延迟导入 CrewAI 的 LLM 类，避免循环依赖
    from crewai import LLM

    # IBM WatsonX 提供商：使用专用的创建函数
    if provider == PROVIDER_IBM_WATSONX:
        return _create_watsonx_llm(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url_ibm_watsonx or IBM_WATSONX_URLS[0],
            project_id=project_id,
        )

    # Google 提供商：使用 google/ 前缀创建 LLM
    if provider == PROVIDER_GOOGLE:
        return LLM(model=LLM_MODEL_PREFIXES[PROVIDER_GOOGLE] + model_name, api_key=api_key)

    # OpenAI 提供商：使用 openai/ 前缀创建 LLM
    if provider == PROVIDER_OPENAI:
        return LLM(model=LLM_MODEL_PREFIXES[PROVIDER_OPENAI] + model_name, api_key=api_key)

    # Anthropic 提供商：使用 anthropic/ 前缀创建 LLM
    if provider == PROVIDER_ANTHROPIC:
        return LLM(model=LLM_MODEL_PREFIXES[PROVIDER_ANTHROPIC] + model_name, api_key=api_key)

    # Ollama 提供商：使用专用的创建函数（本地部署，无需 API 密钥）
    if provider == PROVIDER_OLLAMA:
        return _create_ollama_llm(model_name=model_name, base_url=ollama_base_url)

    # 不支持的提供商，抛出异常
    raise ValueError(ERROR_UNSUPPORTED_PROVIDER.format(provider=provider))


def _create_watsonx_llm(
    model_name: str,
    api_key: str | None,
    base_url: str,
    project_id: str | None,
) -> LLM:
    """Create IBM WatsonX LLM instance with default parameters.

    Configures temperature, max_tokens, and max_input_tokens to WatsonX defaults.
    """
    # 创建 IBM WatsonX LLM 实例，使用默认参数配置
    # 配置温度、最大输出 token 数和最大输入 token 数为 WatsonX 默认值

    from crewai import LLM

    return LLM(
        model=LLM_MODEL_PREFIXES[PROVIDER_IBM_WATSONX] + model_name,  # 模型名添加 ibm/ 前缀
        base_url=base_url,  # WatsonX API 端点地址
        project_id=project_id,  # WatsonX 项目 ID
        api_key=api_key,  # API 认证密钥
        temperature=WATSONX_DEFAULT_TEMPERATURE,  # 默认温度（控制生成随机性）
        max_tokens=WATSONX_DEFAULT_MAX_TOKENS,  # 默认最大输出 token 数
        max_input_tokens=WATSONX_DEFAULT_MAX_INPUT_TOKENS,  # 默认最大输入 token 数
    )


def _create_ollama_llm(model_name: str, base_url: str | None) -> LLM:
    """Create Ollama LLM instance for local model deployment.

    Uses the provided base URL or defaults to localhost:11434.
    """
    # 创建 Ollama LLM 实例，用于本地模型部署
    # 使用提供的 base_url，如果没有提供则默认使用 localhost:11434

    from crewai import LLM

    return LLM(
        model=LLM_MODEL_PREFIXES[PROVIDER_OLLAMA] + model_name,  # 模型名添加 ollama/ 前缀
        base_url=base_url or DEFAULT_OLLAMA_URL,  # Ollama 服务地址，兜底使用默认本地地址
    )
