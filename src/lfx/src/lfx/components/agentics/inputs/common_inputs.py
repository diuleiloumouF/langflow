"""Common input field definitions shared across Agentics components."""

# 该模块定义了 Agentics 组件之间共享的通用输入字段，
# 包括模型提供商配置、API 密钥、WatsonX 特定字段、Ollama URL 以及生成字段的表格模式定义。

from __future__ import annotations

from lfx.base.models.watsonx_constants import IBM_WATSONX_URLS
from lfx.components.agentics.constants import DEFAULT_OLLAMA_URL
from lfx.io import (
    DropdownInput,
    MessageInput,
    ModelInput,
    SecretStrInput,
    StrInput,
    TableInput,
)
from lfx.schema.table import EditMode

# 生成字段表格的模式定义，用于配置 AI 生成输出的结构（字段名、描述、类型、是否为列表）
GENERATED_FIELDS_TABLE_SCHEMA = [
    {
        "name": "name",
        "display_name": "Name",
        "type": "str",
        "description": "The name of the output field (e.g., 'summary', 'category', 'score').",
        "default": "text",
        "edit_mode": EditMode.INLINE,
    },
    {
        "name": "description",
        "display_name": "Description",
        "type": "str",
        "description": "A clear description of what this field represents and how it should be generated.",
        "default": "",
        "edit_mode": EditMode.POPOVER,
    },
    {
        "name": "type",
        "display_name": "Type",
        "type": "str",
        "edit_mode": EditMode.INLINE,
        "description": "The data type for this field (str, int, float, bool, or dict).",
        "options": ["str", "int", "float", "bool", "dict"],
        "default": "str",
    },
    {
        "name": "multiple",
        "display_name": "As List",
        "type": "boolean",
        "description": "Enable to make this field a list of the specified type (e.g., list[str]).",
        "default": False,
        "edit_mode": EditMode.INLINE,
    },
]

# 生成字段的默认空值，用户可在此基础上添加自定义字段
GENERATED_FIELDS_DEFAULT_VALUE: list[dict[str, str | bool]] = []


# 返回模型提供商配置的标准输入字段集合（模型选择、API 密钥、WatsonX 和 Ollama 特定字段）
def get_model_provider_inputs() -> list:
    """Return the standard set of model provider configuration inputs.

    Includes model selection, API key, and provider-specific fields for
    WatsonX and Ollama.
    """
    return [
        ModelInput(
            name="model",
            display_name="Language Model",
            info="Select your model provider",
            real_time_refresh=True,
            required=True,
        ),
        get_api_key_input(),
        *get_watsonx_inputs(),
        get_ollama_url_input(),
    ]


# 返回用于提供商身份验证的 API 密钥输入字段
def get_api_key_input() -> SecretStrInput:
    """Return the API key input field for provider authentication."""
    return SecretStrInput(
        name="api_key",
        display_name="API Key",
        info="Overrides global provider settings. Leave blank to use your pre-configured API Key.",
        real_time_refresh=True,
        advanced=True,
    )


# 返回 IBM WatsonX 特定的配置输入字段（API 端点选择和项目 ID）
def get_watsonx_inputs() -> list:
    """Return IBM WatsonX-specific configuration inputs.

    Includes API endpoint selection and project ID fields.
    """
    return [
        DropdownInput(
            name="base_url_ibm_watsonx",
            display_name="Watsonx API Endpoint",
            info="API endpoint URL for IBM WatsonX (shown only when WatsonX is selected).",
            options=IBM_WATSONX_URLS,
            value=IBM_WATSONX_URLS[0],
            show=False,
            real_time_refresh=True,
        ),
        StrInput(
            name="project_id",
            display_name="Watsonx Project ID",
            info="Project ID for IBM WatsonX workspace (shown only when WatsonX is selected).",
            show=False,
            required=False,
        ),
    ]


# 返回用于本地模型部署的 Ollama 基础 URL 输入字段
def get_ollama_url_input() -> MessageInput:
    """Return the Ollama base URL input for local model deployment."""
    return MessageInput(
        name="ollama_base_url",
        display_name="Ollama API URL",
        info=f"API endpoint for Ollama (shown only when Ollama is selected). Defaults to {DEFAULT_OLLAMA_URL}.",
        value=DEFAULT_OLLAMA_URL,
        show=False,
        real_time_refresh=True,
        load_from_db=True,
    )


# 返回用于定义生成字段的输出 schema 表格输入
def get_generated_fields_input(
    name: str = "schema",
    display_name: str = "Schema",
    info: str = ("Define the structure of data to generate. Specify column names, descriptions, and types."),
    *,
    required: bool = True,
) -> TableInput:
    """Return the output schema table input for defining generated fields.

    Allows users to specify field names, descriptions, types, and whether
    fields should be lists.
    """
    return TableInput(
        name=name,
        display_name=display_name,
        info=info,
        required=required,
        table_schema=GENERATED_FIELDS_TABLE_SCHEMA,
        value=GENERATED_FIELDS_DEFAULT_VALUE,
    )
