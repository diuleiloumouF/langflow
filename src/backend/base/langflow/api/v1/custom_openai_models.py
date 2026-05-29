from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, field_validator

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.variable.model import VariableUpdate
from langflow.services.deps import get_variable_service
from langflow.services.variable.base import VariableService
from langflow.services.variable.constants import CREDENTIAL_TYPE, GENERIC_TYPE

CUSTOM_OPENAI_MODELS_VAR = "__custom_openai_compatible_models__"

CUSTOM_OPENAI_PROVIDER = "Custom OpenAI Compatible"
CUSTOM_OPENAI_PROVIDER_ICON = "OpenAI"
CUSTOM_OPENAI_PROVIDER_DOCS_URL = "https://platform.openai.com/docs/api-reference"

MAX_CUSTOM_MODELS = 100


class CustomOpenAIModelConfig(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    model_name: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str = Field(min_length=1, max_length=500)
    model_type: str = Field(default="llm")
    enabled_by_default: bool = Field(default=False)

    @field_validator("id", "model_name", "display_name", "base_url", "api_key")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            msg = "Field cannot be empty"
            raise ValueError(msg)
        return stripped

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"llm", "embeddings"}:
            msg = "model_type must be 'llm' or 'embeddings'"
            raise ValueError(msg)
        return normalized


class CustomOpenAIModelUpsertRequest(BaseModel):
    id: str | None = Field(default=None, max_length=120)
    model_name: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str | None = Field(default=None, max_length=500)
    model_type: str = Field(default="llm")
    enabled_by_default: bool = Field(default=False)

    @field_validator("id")
    @classmethod
    def strip_optional_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("model_name", "display_name", "base_url")
    @classmethod
    def strip_required_fields(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            msg = "Field cannot be empty"
            raise ValueError(msg)
        return stripped

    @field_validator("api_key")
    @classmethod
    def strip_optional_api_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("model_type")
    @classmethod
    def normalize_model_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"llm", "embeddings"}:
            msg = "model_type must be 'llm' or 'embeddings'"
            raise ValueError(msg)
        return normalized


class CustomOpenAIModelRead(BaseModel):
    id: str
    model_name: str
    display_name: str
    base_url: str
    api_key: str | None = None
    has_api_key: bool
    model_type: str
    enabled_by_default: bool


@dataclass
class CustomOpenAIModelRuntime:
    id: str
    model_name: str
    display_name: str
    base_url: str
    api_key: str
    model_type: str
    enabled_by_default: bool


_MIN_SECRET_DISPLAY_LEN = 8


def _mask_secret(value: str) -> str:
    if len(value) <= _MIN_SECRET_DISPLAY_LEN:
        return "•" * len(value)
    return f"{value[:4]}{'•' * max(len(value) - _MIN_SECRET_DISPLAY_LEN, 4)}{value[-4:]}"


def build_custom_model_variable_name(model_id: str, field: str) -> str:
    return f"__custom_openai_model__::{model_id}::{field}"


async def get_custom_openai_models(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
    include_secrets: bool = False,
) -> list[CustomOpenAIModelRead]:
    configs = await _load_custom_openai_model_configs(
        session=session,
        current_user=current_user,
    )
    variable_service = get_variable_service()

    api_keys_by_id: dict[str, str] = {}
    if variable_service is not None:
        for config in configs:
            try:
                api_key = await variable_service.get_variable(
                    user_id=current_user.id,
                    name=build_custom_model_variable_name(config.id, "api_key"),
                    field="",
                    session=session,
                )
            except ValueError:
                api_key = ""
            api_keys_by_id[config.id] = api_key

    result = []
    for config in configs:
        api_key = api_keys_by_id.get(config.id, "")
        result.append(
            CustomOpenAIModelRead(
                id=config.id,
                model_name=config.model_name,
                display_name=config.display_name,
                base_url=config.base_url,
                api_key=api_key if include_secrets else (_mask_secret(api_key) if api_key else None),
                has_api_key=bool(api_key),
                model_type=config.model_type,
                enabled_by_default=config.enabled_by_default,
            )
        )
    return result


async def get_custom_openai_model_runtimes(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> list[CustomOpenAIModelRuntime]:
    configs = await _load_custom_openai_model_configs(
        session=session,
        current_user=current_user,
    )
    variable_service = get_variable_service()
    if variable_service is None:
        return []

    runtimes: list[CustomOpenAIModelRuntime] = []
    for config in configs:
        try:
            api_key = await variable_service.get_variable(
                user_id=current_user.id,
                name=build_custom_model_variable_name(config.id, "api_key"),
                field="",
                session=session,
            )
        except ValueError:
            api_key = ""

        if not api_key:
            continue

        runtimes.append(
            CustomOpenAIModelRuntime(
                id=config.id,
                model_name=config.model_name,
                display_name=config.display_name,
                base_url=config.base_url,
                api_key=api_key,
                model_type=config.model_type,
                enabled_by_default=config.enabled_by_default,
            )
        )

    return runtimes


async def upsert_custom_openai_model(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
    request: CustomOpenAIModelUpsertRequest,
) -> CustomOpenAIModelRead:
    variable_service = _require_variable_service(get_variable_service())
    configs = await _load_custom_openai_model_configs(
        session=session,
        current_user=current_user,
    )

    model_id = request.id or _slugify_model_id(request.display_name, request.model_name)
    existing_config = next((config for config in configs if config.id == model_id), None)
    existing_api_key = None
    if existing_config is not None:
        try:
            existing_api_key = await variable_service.get_variable(
                user_id=current_user.id,
                name=build_custom_model_variable_name(model_id, "api_key"),
                field="",
                session=session,
            )
        except ValueError:
            existing_api_key = None

    resolved_api_key = request.api_key or existing_api_key
    if not resolved_api_key:
        msg = "API key is required."
        raise ValueError(msg)

    new_config = CustomOpenAIModelConfig(
        id=model_id,
        model_name=request.model_name,
        display_name=request.display_name,
        base_url=request.base_url,
        api_key=resolved_api_key,
        model_type=request.model_type,
        enabled_by_default=request.enabled_by_default,
    )

    existing_index = next((i for i, config in enumerate(configs) if config.id == model_id), None)
    if existing_index is None and len(configs) >= MAX_CUSTOM_MODELS:
        msg = f"You can store at most {MAX_CUSTOM_MODELS} custom OpenAI compatible models."
        raise ValueError(msg)

    for config in configs:
        if config.id != model_id and config.display_name.lower() == new_config.display_name.lower():
            msg = "A custom model with the same display name already exists."
            raise ValueError(msg)

    persisted_config = new_config.model_copy(update={"api_key": "stored"})
    if existing_index is None:
        configs.append(persisted_config)
    else:
        configs[existing_index] = persisted_config

    await _save_custom_openai_model_configs(
        variable_service=variable_service,
        session=session,
        current_user=current_user,
        configs=configs,
    )
    await _save_custom_openai_model_api_key(
        variable_service=variable_service,
        session=session,
        current_user=current_user,
        model_id=model_id,
        api_key=resolved_api_key,
    )

    return CustomOpenAIModelRead(
        id=model_id,
        model_name=request.model_name,
        display_name=request.display_name,
        base_url=request.base_url,
        api_key=_mask_secret(resolved_api_key),
        has_api_key=True,
        model_type=request.model_type,
        enabled_by_default=request.enabled_by_default,
    )


async def delete_custom_openai_model(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
    model_id: str,
) -> None:
    variable_service = _require_variable_service(get_variable_service())
    configs = await _load_custom_openai_model_configs(
        session=session,
        current_user=current_user,
    )

    remaining_configs = [config for config in configs if config.id != model_id]
    if len(remaining_configs) == len(configs):
        msg = f"Custom model '{model_id}' not found."
        raise ValueError(msg)

    await _save_custom_openai_model_configs(
        variable_service=variable_service,
        session=session,
        current_user=current_user,
        configs=remaining_configs,
    )
    with contextlib.suppress(ValueError):
        await variable_service.delete_variable(
            user_id=current_user.id,
            name=build_custom_model_variable_name(model_id, "api_key"),
            session=session,
        )


async def _load_custom_openai_model_configs(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> list[CustomOpenAIModelConfig]:
    variable_service = get_variable_service()
    if variable_service is None:
        return []

    try:
        raw_value = await variable_service.get_variable(
            user_id=current_user.id,
            name=CUSTOM_OPENAI_MODELS_VAR,
            field="",
            session=session,
        )
    except ValueError:
        return []

    if not raw_value:
        return []

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return []

    if not isinstance(parsed, list):
        return []

    configs: list[CustomOpenAIModelConfig] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        try:
            configs.append(CustomOpenAIModelConfig.model_validate(item))
        except (ValueError, TypeError):
            continue
    return configs


async def _save_custom_openai_model_configs(
    *,
    variable_service: VariableService,
    session: DbSession,
    current_user: CurrentActiveUser,
    configs: list[CustomOpenAIModelConfig],
) -> None:
    serialized_configs = json.dumps(
        [config.model_dump(mode="json") for config in configs],
    )

    try:
        existing_var = await variable_service.get_variable_object(
            user_id=current_user.id,
            name=CUSTOM_OPENAI_MODELS_VAR,
            session=session,
        )
    except ValueError:
        existing_var = None

    if existing_var and existing_var.id is not None:
        await variable_service.update_variable_fields(
            user_id=current_user.id,
            variable_id=existing_var.id,
            variable=VariableUpdate(
                id=existing_var.id,
                name=CUSTOM_OPENAI_MODELS_VAR,
                value=serialized_configs,
                type=GENERIC_TYPE,
            ),
            session=session,
        )
        return

    await variable_service.create_variable(
        user_id=current_user.id,
        name=CUSTOM_OPENAI_MODELS_VAR,
        value=serialized_configs,
        default_fields=[],
        type_=GENERIC_TYPE,
        session=session,
    )


async def _save_custom_openai_model_api_key(
    *,
    variable_service: VariableService,
    session: DbSession,
    current_user: CurrentActiveUser,
    model_id: str,
    api_key: str,
) -> None:
    variable_name = build_custom_model_variable_name(model_id, "api_key")

    try:
        existing_var = await variable_service.get_variable_object(
            user_id=current_user.id,
            name=variable_name,
            session=session,
        )
    except ValueError:
        existing_var = None

    if existing_var and existing_var.id is not None:
        await variable_service.update_variable_fields(
            user_id=current_user.id,
            variable_id=existing_var.id,
            variable=VariableUpdate(
                id=existing_var.id,
                name=variable_name,
                value=api_key,
                type=CREDENTIAL_TYPE,
            ),
            session=session,
        )
        return

    await variable_service.create_variable(
        user_id=current_user.id,
        name=variable_name,
        value=api_key,
        default_fields=[],
        type_=CREDENTIAL_TYPE,
        session=session,
    )


def _slugify_model_id(display_name: str, model_name: str) -> str:
    import re

    seed = f"{display_name}-{model_name}".lower()
    slug = re.sub(r"[^a-z0-9]+", "-", seed).strip("-")
    return slug[:120] or "custom-openai-model"


def _require_variable_service(variable_service: VariableService | None) -> VariableService:
    if variable_service is None:
        msg = "Variable service is not available."
        raise ValueError(msg)
    return variable_service


def build_custom_openai_provider_payload(
    runtime_models: list[CustomOpenAIModelRuntime],
) -> dict[str, Any] | None:
    if not runtime_models:
        return None

    return {
        "provider": CUSTOM_OPENAI_PROVIDER,
        "icon": CUSTOM_OPENAI_PROVIDER_ICON,
        "api_docs_url": CUSTOM_OPENAI_PROVIDER_DOCS_URL,
        "models": [
            {
                "id": model.id,
                "model_name": model.model_name,
                "metadata": {
                    "default": model.enabled_by_default,
                    "model_type": model.model_type,
                    "is_custom_openai_compatible": True,
                    "custom_openai_model_id": model.id,
                    "display_name": model.display_name,
                    "api_key_param": "api_key",
                    "model_name_param": "model",
                    "model_class": "ChatOpenAI" if model.model_type == "llm" else "OpenAIEmbeddings",
                    "param_mapping": {
                        "model": "model",
                        "api_key": "api_key",
                        "api_base": "base_url",
                        "dimensions": "dimensions",
                        "chunk_size": "chunk_size",
                        "request_timeout": "timeout",
                        "max_retries": "max_retries",
                        "show_progress_bar": "show_progress_bar",
                        "model_kwargs": "model_kwargs",
                    },
                    "custom_openai_base_url": model.base_url,
                    "custom_openai_api_key": model.api_key,
                },
            }
            for model in runtime_models
        ],
    }
