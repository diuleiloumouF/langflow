from unittest import mock

import pytest
from httpx import AsyncClient


@pytest.mark.usefixtures("active_user")
@pytest.mark.asyncio
async def test_custom_openai_model_crud_and_models_endpoint(
    client: AsyncClient,
    logged_in_headers,
):
    payload = {
        "model_name": "gpt-4o-mini",
        "display_name": "My OpenAI Proxy",
        "base_url": "https://example.test/v1",
        "api_key": "sk-custom-test-123456",  # pragma: allowlist secret
        "model_type": "llm",
        "enabled_by_default": True,
    }

    create_response = await client.post(
        "api/v1/models/custom-openai-models",
        json=payload,
        headers=logged_in_headers,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["display_name"] == "My OpenAI Proxy"
    assert created["has_api_key"] is True

    list_response = await client.get(
        "api/v1/models/custom-openai-models",
        headers=logged_in_headers,
    )
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["display_name"] == "My OpenAI Proxy"
    assert listed[0]["api_key"] is not None

    models_response = await client.get("api/v1/models", headers=logged_in_headers)
    assert models_response.status_code == 200
    providers = models_response.json()
    custom_provider = next(provider for provider in providers if provider["provider"] == "Custom OpenAI Compatible")
    assert custom_provider["is_configured"] is True
    assert custom_provider["is_enabled"] is True
    assert custom_provider["models"][0]["id"] == created["id"]
    assert custom_provider["models"][0]["metadata"]["display_name"] == "My OpenAI Proxy"

    enabled_response = await client.get(
        "api/v1/models/enabled_models",
        headers=logged_in_headers,
    )
    assert enabled_response.status_code == 200
    enabled_models = enabled_response.json()["enabled_models"]
    assert enabled_models["Custom OpenAI Compatible"][created["id"]] is True

    delete_response = await client.delete(
        f"api/v1/models/custom-openai-models/{created['id']}",
        headers=logged_in_headers,
    )
    assert delete_response.status_code == 204


def test_custom_openai_instantiation_uses_runtime_credentials():
    from lfx.base.models.unified_models.instantiation import get_llm

    captured_kwargs = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    with (
        mock.patch(
            "lfx.base.models.unified_models.get_model_class",
            return_value=FakeChatOpenAI,
        ),
        mock.patch(
            "lfx.base.models.unified_models.get_api_key_for_provider",
            return_value="ignored-shared-key",
        ),
    ):
        result = get_llm(
            model=[
                {
                    "name": "gpt-4o-mini",
                    "provider": "Custom OpenAI Compatible",
                    "metadata": {
                        "is_custom_openai_compatible": True,
                        "custom_openai_api_key": "sk-custom-runtime",  # pragma: allowlist secret
                        "custom_openai_base_url": "https://proxy.example/v1",
                        "model_class": "ChatOpenAI",
                        "model_name_param": "model",
                        "api_key_param": "api_key",  # pragma: allowlist secret
                    },
                }
            ],
            user_id=None,
        )

    assert isinstance(result, FakeChatOpenAI)
    assert captured_kwargs["model"] == "gpt-4o-mini"
    assert captured_kwargs["api_key"] == "sk-custom-runtime"  # pragma: allowlist secret
    assert captured_kwargs["base_url"] == "https://proxy.example/v1"


def test_model_relay_instantiation_uses_default_base_url():
    from lfx.base.models.unified_models.instantiation import get_llm

    captured_kwargs = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    with (
        mock.patch(
            "lfx.base.models.unified_models.get_model_class",
            return_value=FakeChatOpenAI,
        ),
        mock.patch(
            "lfx.base.models.unified_models.get_api_key_for_provider",
            return_value="sk-model-relay-runtime",  # pragma: allowlist secret
        ),
    ):
        result = get_llm(
            model=[
                {
                    "name": "text-general-pro",
                    "provider": "Model Relay",
                    "metadata": {
                        "model_class": "ChatOpenAI",
                        "model_name_param": "model",
                        "api_key_param": "api_key",  # pragma: allowlist secret
                    },
                }
            ],
            user_id=None,
        )

    assert isinstance(result, FakeChatOpenAI)
    assert captured_kwargs["model"] == "text-general-pro"
    assert captured_kwargs["api_key"] == "sk-model-relay-runtime"  # pragma: allowlist secret
    assert captured_kwargs["base_url"] == "https://model-relay-api.zzengine.net/v1"
