from __future__ import annotations

from typing import Any

from lfx.components.modelrelay.client import (
    MODEL_RELAY_API_KEY_VARIABLE,
    extract_task_uid,
    get_task_query,
    resolve_api_key,
)
from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageTextInput, Output, SecretStrInput
from lfx.log.logger import logger
from lfx.schema.data import Data


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
    ]

    outputs = [Output(display_name="Task Result", name="task_result", method="query_task")]

    def query_task(self) -> Data:
        api_key = resolve_api_key(self.api_key, self.user_id)
        task_uid = extract_task_uid(getattr(self, "task_uid", None)) or extract_task_uid(getattr(self, "task", None))
        if not task_uid:
            msg = "Task UID is required, either directly or from Task Data."
            raise ValueError(msg)

        try:
            response = get_task_query(api_key, task_uid)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Error querying Model Relay task", exc_info=True)
            self.status = f"Model Relay task query failed: {exc}"
            return Data(data={"error": str(exc), "task_uid": task_uid})

        output = self._flatten_query_response(response)
        result = Data(data=output)
        self.status = result
        return result

    @staticmethod
    def _flatten_query_response(response: dict[str, Any]) -> dict[str, Any]:
        data = response.get("data") if isinstance(response.get("data"), dict) else {}
        task = data.get("task") if isinstance(data.get("task"), dict) else {}
        detail = task.get("detail") if isinstance(task.get("detail"), dict) else {}
        result = detail.get("result")
        return {
            "response": response,
            "task": task,
            "result": result,
        }
