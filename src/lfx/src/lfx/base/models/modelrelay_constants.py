from .model_metadata import create_model_metadata

MODEL_RELAY_PROVIDER = "Model Relay"
MODEL_RELAY_API_KEY = "MODEL_RELAY_API_KEY"  # pragma: allowlist secret
MODEL_RELAY_BASE_URL = "https://model-relay-api.zzengine.net"
MODEL_RELAY_OPENAI_BASE_URL = f"{MODEL_RELAY_BASE_URL}/v1"

MODEL_RELAY_MODELS_DETAILED = [
    create_model_metadata(provider=MODEL_RELAY_PROVIDER, name="gpt-5.4", icon="Network", tool_calling=True),
    create_model_metadata(
        provider=MODEL_RELAY_PROVIDER, name="gemini-3.1-pro-preview", icon="Network", tool_calling=True
    ),
    create_model_metadata(provider=MODEL_RELAY_PROVIDER, name="claude-sonnet-4-6", icon="Network", tool_calling=True),
    # create_model_metadata(provider=MODEL_RELAY_PROVIDER, name="claude-sonnet-4", icon="Network", tool_calling=True),
]

MODEL_RELAY_MODELS = [metadata["name"] for metadata in MODEL_RELAY_MODELS_DETAILED]
