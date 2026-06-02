"""LLM setup and configuration utilities for Agentics components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from lfx.base.models.unified_models import get_api_key_for_provider
from lfx.components.agentics.constants import (
    ERROR_API_KEY_REQUIRED,
    PROVIDER_OLLAMA,
)
from lfx.components.agentics.helpers.llm_factory import create_llm
from lfx.components.agentics.helpers.model_config import validate_model_selection

if TYPE_CHECKING:
    from crewai import LLM

    from lfx.custom.custom_component.component import Component


def prepare_llm_from_component(component: Component) -> LLM:
    """Prepare and configure an LLM instance from component settings.

    Extracts model selection, validates configuration, retrieves API keys,
    and creates a fully configured LLM instance ready for use.

    Args:
        component: The Agentics component instance containing model configuration.

    Returns:
        Configured LLM instance with all provider-specific settings applied.

    Raises:
        ValueError: If model is not selected or required API key is missing for the provider.
    """
    # 验证组件中选择的模型，获取模型名称和对应的提供商
    model_name, provider = validate_model_selection(component.model)
    # 根据提供商获取对应的 API 密钥（支持用户手动输入或从环境变量读取）
    api_key = get_api_key_for_provider(component.user_id, provider, component.api_key)

    # 如果不是本地 Ollama 服务且未找到 API 密钥，则抛出错误
    if not api_key and provider != PROVIDER_OLLAMA:
        raise ValueError(ERROR_API_KEY_REQUIRED.format(provider=provider))

    # 调用工厂方法创建并返回完全配置好的 LLM 实例
    return create_llm(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url_ibm_watsonx=getattr(component, "base_url_ibm_watsonx", None),
        project_id=getattr(component, "project_id", None),
        ollama_base_url=getattr(component, "ollama_base_url", None),
    )
