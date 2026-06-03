# Feature: Model Relay API Integration

> Generated on: 2026-06-03
> Status: Planned / Implemented in downstream customization
> Owner: AI Platform Integration

## Overview

This change adds a company-owned Model Relay provider to Langflow while preserving existing official AI provider integrations. The relay is exposed to builders through the existing model provider settings page and through canvas components for asynchronous media tasks.

## Requirements

- Add `Model Relay` as an additional model provider without changing OpenAI, Anthropic, Google, or other official provider behavior.
- Store the relay API key from `/settings/model-providers` using the existing Global Variables credential mechanism.
- Use `MODEL_RELAY_API_KEY` as the credential variable name.
- Use the fixed relay base URL `https://model-relay-api.zzengine.net`.
- Support regular and streaming text chat through the relay OpenAI-compatible endpoint: `POST /v1/chat/completions`.
- Support image and video task creation through `POST /api/v1/task/submit`.
- Support image and video task lookup through `GET /api/v1/task/query`.
- Keep media tasks split into submit and query components so long-running jobs do not block a flow run by default.

## User-Facing Behavior

- Users configure the relay key in `/settings/model-providers` under `Model Relay`.
- The `Language Model` selector can show relay text models after the provider is configured.
- Initial relay text models are `text-general-pro`, `openai-gpt-4o`, `gemini-2.5-pro`, and `claude-sonnet-4`.
- `Model Relay Submit Task` submits an image or video task and exposes `task_uid` as the primary output for direct wiring.
- `Model Relay Query Task` accepts the submit component's `task_uid` output directly, or a manually entered task UID, and returns the raw task detail.

## API Contracts

- Text chat uses `https://model-relay-api.zzengine.net/v1/chat/completions` through LangChain `ChatOpenAI`.
- Task submission sends `X-Api-Key` and a JSON body with `task_type`, `model_code`, `prompt`, optional media fields, and optional `parameters`.
- Task query sends `X-Api-Key` and `task_uid` as a query parameter.
- Submit exposes `task_uid` as the primary output and also preserves the raw relay response under the `Task Data` output.
- Query outputs preserve the raw relay response under `response`; convenience fields are additive only.

## Acceptance Criteria

- `Model Relay` appears in the model provider mapping API with `MODEL_RELAY_API_KEY`.
- Saving `MODEL_RELAY_API_KEY` marks `Model Relay` configured.
- Selecting a relay text model instantiates `ChatOpenAI` with `base_url=https://model-relay-api.zzengine.net/v1`.
- Submit and query components can be added to the canvas and wired together from `Task UID` to `Task UID`.
- Existing official provider channels continue to behave unchanged.
