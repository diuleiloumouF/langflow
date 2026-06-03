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
- Relay text models are defined by `MODEL_RELAY_MODELS_DETAILED`; the current configured models are `gpt-5.4`, `gemini-3.1-pro-preview`, and `claude-sonnet-4-6`.
- `Model Relay Submit Task` submits an image or video task and exposes `task_uid` as the primary output for direct wiring.
- `Model Relay Query Task` accepts the submit component's `task_uid` output directly, or a manually entered task UID, and returns the raw task detail.
- `Model Relay Query Task` exposes `Task Media` as a message output for image/video results so builders can connect it to chat output and preview generated media.
- `Model Relay Query Task` supports optional polling for asynchronous image/video tasks until status `2` success, status `3` failure, or the configured attempt limit is reached.

## API Contracts

- Text chat uses `https://model-relay-api.zzengine.net/v1/chat/completions` through LangChain `ChatOpenAI`.
- Task submission sends `X-Api-Key` and a JSON body with `task_type`, `model_code`, `prompt`, optional media fields, and optional `parameters`.
- Task query sends `X-Api-Key` and `task_uid` as a query parameter.
- Submit exposes `task_uid` as the primary output and also preserves the raw relay response under the `Task Data` output.
- Query outputs preserve the raw relay response under `response`; convenience fields are additive only.
- Query media output extracts common result fields such as `video`, `videos`, `image`, `images`, `image_url`, `image_urls`, and compatible URL lists from `detail.result`.
- Query polling is disabled by default to preserve existing single-query behavior. When enabled, `max_attempts` and `poll_interval_seconds` control how long the component waits.

## Acceptance Criteria

- `Model Relay` appears in the model provider mapping API with `MODEL_RELAY_API_KEY`.
- Saving `MODEL_RELAY_API_KEY` marks `Model Relay` configured.
- Selecting a relay text model instantiates `ChatOpenAI` with `base_url=https://model-relay-api.zzengine.net/v1`.
- Submit and query components can be added to the canvas and wired together from `Task UID` to `Task UID`.
- Query can optionally poll asynchronous media tasks and returns the last task response with `attempts` and `completed` convenience fields.
- Query can output generated image/video media as a message that renders through the chat/media display path.
- Existing official provider channels continue to behave unchanged.
