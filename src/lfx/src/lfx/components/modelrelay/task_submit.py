from __future__ import annotations

from typing import Any

from lfx.components.modelrelay.client import (
    MODEL_RELAY_API_KEY_VARIABLE,
    extract_text,
    post_task_submit,
    resolve_api_key,
)
from lfx.custom.custom_component.component import Component
from lfx.io import DictInput, DropdownInput, IntInput, MessageTextInput, Output, SecretStrInput
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.message import Message


class ModelRelayTaskSubmitComponent(Component):
    display_name = "Model Relay Submit Task"
    description = "Submit image or video generation tasks to Model Relay and return the task UID."
    documentation = "https://model-relay-api.zzengine.net"
    icon = "Network"
    name = "ModelRelayTaskSubmit"

    inputs = [
        SecretStrInput(
            name="api_key",
            display_name="Model Relay API Key",
            value=MODEL_RELAY_API_KEY_VARIABLE,
            required=True,
            info="Falls back to MODEL_RELAY_API_KEY from Model providers or environment variables.",
        ),
        DropdownInput(
            name="task_type",
            display_name="Task Type",
            options=["image", "video"],
            value="image",
            required=True,
            real_time_refresh=True,
        ),
        MessageTextInput(name="model_code", display_name="Model Code", required=True),
        MessageTextInput(name="prompt", display_name="Prompt", required=True, tool_mode=True),
        MessageTextInput(name="callback_url", display_name="Callback URL", advanced=True),
        IntInput(name="image_width", display_name="Image Width", advanced=True),
        IntInput(name="image_height", display_name="Image Height", advanced=True),
        IntInput(name="video_duration", display_name="Video Duration", advanced=True),
        MessageTextInput(name="video_resolution", display_name="Video Resolution", advanced=True),
        MessageTextInput(name="video_ratio", display_name="Video Ratio", advanced=True),
        DictInput(
            name="parameters",
            display_name="Parameters",
            advanced=True,
            info="Additional task parameters passed through to Model Relay.",
        ),
    ]

    outputs = [
        Output(display_name="Task UID", name="task_uid", method="submit_task_uid"),
        Output(display_name="Task Data", name="task", method="submit_task"),
    ]

    def submit_task(self) -> Data:
        return self._submit_task()

    def submit_task_uid(self) -> Message:
        result = self._submit_task()
        return Message(text=str(result.data.get("task_uid") or ""))

    def _submit_task(self) -> Data:
        if hasattr(self, "_submission_result"):
            return self._submission_result

        api_key = resolve_api_key(self.api_key, self.user_id)
        payload = self._build_payload()

        try:
            response = post_task_submit(api_key, payload)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Error submitting Model Relay task", exc_info=True)
            self.status = f"Model Relay task submission failed: {exc}"
            result = Data(data={"error": str(exc), "request": payload})
            self._submission_result = result
            return result

        output = self._flatten_submit_response(response)
        result = Data(data=output)
        self.status = result
        self._submission_result = result
        return result

    def _build_payload(self) -> dict[str, Any]:
        if self.task_type not in {"image", "video"}:
            msg = "Task Type must be image or video."
            raise ValueError(msg)
        model_code = extract_text(getattr(self, "model_code", None))
        prompt = extract_text(getattr(self, "prompt", None))

        if not model_code:
            msg = "Model Code is required."
            raise ValueError(msg)
        if not prompt:
            msg = "Prompt is required."
            raise ValueError(msg)

        payload: dict[str, Any] = {
            "task_type": self.task_type,
            "model_code": model_code,
            "prompt": prompt,
        }
        callback_url = extract_text(getattr(self, "callback_url", None))
        if callback_url:
            payload["callback_url"] = callback_url
        if getattr(self, "image_width", None):
            payload["image_width"] = self.image_width
        if getattr(self, "image_height", None):
            payload["image_height"] = self.image_height
        if getattr(self, "video_duration", None):
            payload["video_duration"] = self.video_duration
        video_resolution = extract_text(getattr(self, "video_resolution", None))
        if video_resolution:
            payload["video_resolution"] = video_resolution
        video_ratio = extract_text(getattr(self, "video_ratio", None))
        if video_ratio:
            payload["video_ratio"] = video_ratio
        if getattr(self, "parameters", None):
            payload["parameters"] = self.parameters
        return payload

    @staticmethod
    def _flatten_submit_response(response: dict[str, Any]) -> dict[str, Any]:
        data = response.get("data") if isinstance(response.get("data"), dict) else {}
        return {
            "response": response,
            "task_uid": data.get("task_uid"),
            "estimated_amount": data.get("estimated_amount"),
            "account_uid": data.get("account_uid"),
            "key_uid": data.get("key_uid"),
        }

    def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        if field_name == "task_type":
            is_image = field_value == "image"
            for field in ("image_width", "image_height"):
                if field in build_config:
                    build_config[field]["show"] = is_image
            for field in ("video_duration", "video_resolution", "video_ratio"):
                if field in build_config:
                    build_config[field]["show"] = not is_image
        return build_config
