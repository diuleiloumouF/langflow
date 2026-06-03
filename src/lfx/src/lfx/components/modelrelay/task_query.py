from __future__ import annotations

import time
from typing import Any

from lfx.components.modelrelay.client import (
    MODEL_RELAY_API_KEY_VARIABLE,
    extract_task_uid,
    get_task_query,
    resolve_api_key,
)
from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, DataInput, FloatInput, IntInput, MessageTextInput, Output, SecretStrInput
from lfx.log.logger import logger
from lfx.schema.content_block import ContentBlock
from lfx.schema.content_types import MediaContent
from lfx.schema.data import Data
from lfx.schema.message import Message

MODEL_RELAY_TASK_SUCCESS_STATUS = 2
MODEL_RELAY_TASK_FAILURE_STATUS = 3


class ModelRelayTaskQueryComponent(Component):
    display_name = "Model Relay Query Task"
    description = "Query a Model Relay image or video task by task UID."
    documentation = "https://model-relay-api.zzengine.net"
    icon = "Network"
    name = "ModelRelayTaskQuery"

    inputs = [
        SecretStrInput(
            name="api_key",
            display_name="Model Relay API Key",
            value=MODEL_RELAY_API_KEY_VARIABLE,
            required=True,
            info="Falls back to MODEL_RELAY_API_KEY from Model providers or environment variables.",
        ),
        MessageTextInput(name="task_uid", display_name="Task UID", tool_mode=True),
        DataInput(
            name="task",
            display_name="Task Data",
            info="Optional output from Model Relay Submit Task. Used when Task UID is empty.",
            advanced=True,
        ),
        BoolInput(
            name="poll_until_complete",
            display_name="Poll Until Complete",
            value=False,
            advanced=True,
            info="Poll until status is 2 (success), 3 (failure), or the max attempts limit is reached.",
        ),
        IntInput(
            name="max_attempts",
            display_name="Max Poll Attempts",
            value=10,
            advanced=True,
            info="Maximum query attempts when polling is enabled.",
        ),
        FloatInput(
            name="poll_interval_seconds",
            display_name="Poll Interval Seconds",
            value=3.0,
            advanced=True,
            info="Seconds to wait between polling attempts.",
        ),
    ]

    outputs = [
        Output(display_name="Task Result", name="task_result", method="query_task"),
        Output(display_name="Task Media", name="task_media", method="query_task_media"),
    ]

    def query_task(self) -> Data:
        result = self._query_task_data()
        self.status = result
        return result

    def query_task_media(self) -> Message:
        result = self._query_task_data()
        if "error" in result.data:
            return Message(text=str(result.data["error"]), error=True)

        task = result.data.get("task") if isinstance(result.data.get("task"), dict) else {}
        media_urls = self._extract_media_urls(result.data.get("result"), task.get("task_type"))
        if not media_urls:
            status = task.get("status")
            return Message(text=f"No media result is available yet. Task status: {status}")

        task_uid = task.get("task_uid") or result.data.get("task_uid") or ""
        caption = f"Model Relay task result {task_uid}".strip()
        message = Message(
            text="",
            content_blocks=[
                ContentBlock(
                    title="Model Relay Media",
                    contents=[MediaContent(type="media", urls=media_urls, caption=caption)],
                )
            ],
        )
        self.status = message
        return message

    def _query_task_data(self) -> Data:
        if hasattr(self, "_query_result"):
            return self._query_result

        api_key = resolve_api_key(self.api_key, self.user_id)
        task_uid = extract_task_uid(getattr(self, "task_uid", None)) or extract_task_uid(getattr(self, "task", None))
        if not task_uid:
            msg = "Task UID is required, either directly or from Task Data."
            raise ValueError(msg)

        try:
            response, attempts = self._query_with_optional_polling(api_key, task_uid)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Error querying Model Relay task", exc_info=True)
            self.status = f"Model Relay task query failed: {exc}"
            result = Data(data={"error": str(exc), "task_uid": task_uid})
            self._query_result = result
            return result

        output = self._flatten_query_response(response)
        output["attempts"] = attempts
        output["completed"] = self._is_terminal_status(output.get("task", {}).get("status"))
        result = Data(data=output)
        self._query_result = result
        return result

    def _query_with_optional_polling(self, api_key: str, task_uid: str) -> tuple[dict[str, Any], int]:
        max_attempts = max(1, int(getattr(self, "max_attempts", 1) or 1))
        poll_interval_seconds = max(0.0, float(getattr(self, "poll_interval_seconds", 0.0) or 0.0))
        should_poll = bool(getattr(self, "poll_until_complete", False))
        attempts_limit = max_attempts if should_poll else 1

        response: dict[str, Any] | None = None
        for attempt in range(1, attempts_limit + 1):
            response = get_task_query(api_key, task_uid)
            task = self._extract_task(response)
            if self._is_terminal_status(task.get("status")):
                return response, attempt
            if attempt < attempts_limit and poll_interval_seconds:
                time.sleep(poll_interval_seconds)

        if response is None:
            msg = "Model Relay task query returned no response."
            raise ValueError(msg)
        return response, attempts_limit

    @staticmethod
    def _flatten_query_response(response: dict[str, Any]) -> dict[str, Any]:
        task = ModelRelayTaskQueryComponent._extract_task(response)
        detail = task.get("detail") if isinstance(task.get("detail"), dict) else {}
        result = detail.get("result")
        return {
            "response": response,
            "task": task,
            "result": result,
        }

    @staticmethod
    def _extract_task(response: dict[str, Any]) -> dict[str, Any]:
        data = response.get("data") if isinstance(response.get("data"), dict) else {}
        return data.get("task") if isinstance(data.get("task"), dict) else {}

    @staticmethod
    def _is_terminal_status(status: Any) -> bool:
        return status in {MODEL_RELAY_TASK_SUCCESS_STATUS, MODEL_RELAY_TASK_FAILURE_STATUS}

    @classmethod
    def _extract_media_urls(cls, value: Any, task_type: Any = None) -> list[str]:
        urls: list[str] = []

        def add_url(candidate: Any, *, key: str | None = None) -> None:
            if not isinstance(candidate, str) or not candidate.strip():
                return
            text = candidate.strip()
            if cls._is_media_url(text):
                urls.append(text)
            elif key == "b64_json" and task_type == "image":
                urls.append(f"data:image/png;base64,{text}")

        def walk(candidate: Any, *, key: str | None = None) -> None:
            if isinstance(candidate, dict):
                preferred_keys = (
                    "video",
                    "videos",
                    "video_url",
                    "video_urls",
                    "image",
                    "images",
                    "image_url",
                    "image_urls",
                    "url",
                    "urls",
                    "b64_json",
                )
                for preferred_key in preferred_keys:
                    if preferred_key in candidate:
                        walk(candidate[preferred_key], key=preferred_key)
                return
            if isinstance(candidate, list):
                for item in candidate:
                    walk(item, key=key)
                return
            add_url(candidate, key=key)

        walk(value)
        return list(dict.fromkeys(urls))

    @staticmethod
    def _is_media_url(value: str) -> bool:
        return value.startswith(("http://", "https://", "data:image/", "data:video/"))
