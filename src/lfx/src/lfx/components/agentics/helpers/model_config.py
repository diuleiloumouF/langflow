# Agentics 组件的模型配置和验证辅助工具
"""Model configuration and validation helpers for Agentics components."""

from __future__ import annotations

import warnings
from typing import Any

from lfx.components.agentics.constants import (
    ERROR_MODEL_NOT_SELECTED,
    PROVIDER_IBM_WATSONX,
    PROVIDER_OLLAMA,
)


# 从组件输入中验证并提取模型名称和提供商
def validate_model_selection(model: Any) -> tuple[str, str]:
    """Validate and extract model name and provider from component input.

    Ensures the model selection is properly formatted and contains required fields.

    Args:
        model: The model selection from the component input (expected as a list with model dict).

    Returns:
        Tuple of (model_name, provider) extracted from the selection.

    Raises:
        ValueError: If no model is selected, model data is invalid, or required fields are missing.
    """
    if not model or not isinstance(model, list) or len(model) == 0:
        raise ValueError(ERROR_MODEL_NOT_SELECTED)

    model_selection = model[0]

    model_name = model_selection.get("name")
    provider = model_selection.get("provider")

    if not model_name or not provider:
        raise ValueError(ERROR_MODEL_NOT_SELECTED)

    return model_name, provider


# ---------------------------------------------------------------------------
# 已弃用 - 仅为了向后兼容而保留
# 这些函数已被 lfx.base.models.unified_models 中的 handle_model_input_update() 取代，
# 后者集中管理所有组件的提供商字段显示/隐藏逻辑。
# 它们将在未来的版本中移除。
# ---------------------------------------------------------------------------


# 已弃用：根据所选模型更新提供商特定字段的可见性
def update_provider_fields_visibility(
    build_config: dict,
    field_value: Any,
    field_name: str | None,
) -> dict:
    """Deprecated. Use handle_model_input_update() from lfx.base.models.unified_models instead.

    Update visibility of provider-specific fields based on the selected model.

    .. deprecated::
        This function was replaced by the unified ``handle_model_input_update()``
        helper, which additionally refreshes model options and pre-populates
        credential fields from the variable service.  Custom components should
        call ``handle_model_input_update(self, build_config, field_value, field_name)``
        from their ``update_build_config`` method instead.
    """
    warnings.warn(
        "update_provider_fields_visibility is deprecated and will be removed in a future release. "
        "Use handle_model_input_update() from lfx.base.models.unified_models instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    current_model_value = field_value if field_name == "model" else build_config.get("model", {}).get("value")

    if not isinstance(current_model_value, list) or len(current_model_value) == 0:
        return build_config

    selected_model = current_model_value[0]
    provider = selected_model.get("provider", "")

    _update_watsonx_fields(build_config, provider)
    _update_ollama_fields(build_config, provider)

    return build_config


# 已弃用的内部辅助函数 - 已被 handle_model_input_update() 吸收
def _update_watsonx_fields(build_config: dict, provider: str) -> None:
    """Deprecated internal helper - absorbed into handle_model_input_update()."""
    is_watsonx = provider == PROVIDER_IBM_WATSONX

    if "base_url_ibm_watsonx" in build_config:
        build_config["base_url_ibm_watsonx"]["show"] = is_watsonx
        build_config["base_url_ibm_watsonx"]["required"] = is_watsonx

    if "project_id" in build_config:
        build_config["project_id"]["show"] = is_watsonx
        build_config["project_id"]["required"] = is_watsonx


# 已弃用的内部辅助函数 - 已被 handle_model_input_update() 吸收
def _update_ollama_fields(build_config: dict, provider: str) -> None:
    """Deprecated internal helper - absorbed into handle_model_input_update()."""
    is_ollama = provider == PROVIDER_OLLAMA

    if "ollama_base_url" in build_config:
        build_config["ollama_base_url"]["show"] = is_ollama
