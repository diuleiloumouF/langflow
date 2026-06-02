"""Name validation, error helpers, and misc utilities for the Watsonx Orchestrate adapter."""
# Watsonx Orchestrate 适配器的名称验证、错误辅助工具及杂项实用函数。

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, NoReturn

from fastapi import HTTPException
from ibm_watsonx_orchestrate_clients.tools.tool_client import ClientAPIException
from lfx.services.adapters.deployment.exceptions import (
    DeploymentError,
    DeploymentServiceError,
    InvalidContentError,
    OperationNotSupportedError,
)
from lfx.services.adapters.deployment.exceptions import (
    raise_as_deployment_error as raise_deployment_error_from_status,
)
from lfx.services.adapters.deployment.schema import _normalize_and_validate_id

from langflow.services.adapters.deployment.watsonx_orchestrate.constants import (
    WXO_SANITIZE_RE,
    WXO_TRANSLATE,
    ErrorPrefix,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from lfx.services.adapters.deployment.schema import (
        ConfigListParams,
        SnapshotListParams,
    )

logger = logging.getLogger(__name__)


def normalize_wxo_name(s: str) -> str:
    # 对 Watsonx Orchestrate 资源名称进行标准化处理：先通过翻译映射替换字符，再移除非法字符。
    return WXO_SANITIZE_RE.sub("", s.translate(WXO_TRANSLATE))


def validate_wxo_name(name: str) -> str:
    """Normalize and validate a wxO resource name."""
    # 标准化并验证 wxO 资源名称，确保名称合法（非空且以字母开头）。
    normalized_name = normalize_wxo_name(str(name))
    if not normalized_name:
        msg = "Deployment name must include at least one alphanumeric character."
        raise InvalidContentError(message=msg)
    if not normalized_name[0].isalpha():
        msg = "Deployment name must start with a letter."
        raise InvalidContentError(message=msg)
    return normalized_name


def require_tool_id(tool_response: dict[str, Any]) -> str:
    # 从工具响应字典中提取 tool id，若不存在则抛出 InvalidContentError。
    tool_id = tool_response.get("id")
    if not tool_id:
        msg = "wxO did not return a tool id for snapshot creation."
        raise InvalidContentError(message=msg)
    return tool_id


def dedupe_list(items: list[str]) -> list[str]:
    # 对字符串列表去重，同时保留原始顺序。
    return list(dict.fromkeys(items))


def normalize_and_dedupe_ids(values: list[Any] | None, *, field_name: str) -> list[str]:
    """Normalize id values to non-empty strings and dedupe while preserving order."""
    # 将 ID 值标准化为非空字符串并去重，同时保留原始顺序。
    if not values:
        return []
    return dedupe_list([_normalize_and_validate_id(str(value), field_name=field_name) for value in values])


def require_single_deployment_id(
    params: ConfigListParams | SnapshotListParams | None,
    *,
    resource_label: str,
) -> str:
    # 要求参数中恰好包含一个 deployment_id，否则抛出异常。
    # watsonx Orchestrate 当前仅支持按单个 deployment_id 进行资源列表查询。
    deployment_ids = params.deployment_ids if params else None
    if not deployment_ids:
        msg = f"watsonx Orchestrate {resource_label} listing requires exactly one deployment_id."
        raise OperationNotSupportedError(message=msg)
    if len(deployment_ids) != 1:
        msg = (
            f"watsonx Orchestrate {resource_label} listing currently supports "
            "exactly one deployment_id and only deployment-scoped listing."
        )
        raise InvalidContentError(message=msg)
    return _normalize_and_validate_id(str(deployment_ids[0]), field_name="deployment_id")


def extract_error_detail(response_text: str) -> str:
    """Extract a human-readable error detail from a ClientAPIException response.

    The response body may contain a ``detail`` value that is a string, a dict
    with a ``msg`` key, or a list of such dicts.  This helper normalises all
    three shapes into a single value suitable for inclusion in an error message.
    """
    # 从 ClientAPIException 响应体中提取可读的错误详情。
    # 响应体中的 ``detail`` 字段可能是字符串、含 ``msg`` 键的字典、
    # 或上述字典的列表。本函数将这三种格式统一为可用于错误消息的字符串。
    fallback = response_text or "<empty response body>"
    try:
        payload = json.loads(response_text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback
    if not isinstance(payload, dict):
        return fallback

    detail = payload.get("detail")
    if detail in (None, "", [], {}):
        for field in ("message", "details", "error"):
            detail = payload.get(field)
            if detail not in (None, "", [], {}):
                break
        else:
            return fallback

    if isinstance(detail, list):
        detail = detail[0] if detail else None
    if isinstance(detail, dict):
        detail = detail.get("msg") or detail

    return str(detail) if detail not in (None, "", [], {}) else fallback


def _resolve_exc_detail(exc: ClientAPIException | HTTPException) -> str:
    # 从异常对象中解析出错误详情字符串。
    if isinstance(exc, ClientAPIException):
        raw_text = getattr(exc.response, "text", "")
        return extract_error_detail(raw_text)
    return str(extract_error_detail(str(exc.detail)))


def _resolve_exc_status_code(exc: ClientAPIException | HTTPException) -> int:
    # 从异常对象中获取 HTTP 状态码。
    if isinstance(exc, ClientAPIException):
        return int(exc.response.status_code)
    return int(exc.status_code)


def raise_as_deployment_error(
    exc: Exception,
    *,
    error_prefix: ErrorPrefix,
    log_msg: str,
    resource: str | None = None,
    resource_name: str | None = None,
    pass_through: tuple[type[DeploymentServiceError], ...] = (),
) -> NoReturn:
    # 将各类异常统一封装为 DeploymentError 后重新抛出。
    # - 若异常类型在 pass_through 中，直接透传不处理。
    # - 若已经是 DeploymentServiceError，记录日志后包装为 DeploymentError。
    # - 若是 ClientAPIException 或 HTTPException，根据状态码生成对应的部署错误。
    # - 其他未知异常统一包装为 DeploymentError。
    if isinstance(exc, pass_through):
        raise exc
    if isinstance(exc, DeploymentServiceError):
        logger.exception(log_msg)
        msg = f"{error_prefix.value} Please check server logs for details."
        raise DeploymentError(message=msg, error_code="deployment_error") from exc
    if isinstance(exc, (ClientAPIException, HTTPException)):
        status_code = _resolve_exc_status_code(exc)
        detail = _resolve_exc_detail(exc)
        raise_deployment_error_from_status(
            status_code=status_code,
            detail=detail,
            message_prefix=error_prefix.value,
            resource=resource,
            resource_name=resource_name,
            cause=exc,
        )
    logger.exception(log_msg)
    msg = f"{error_prefix.value} Please check server logs for details."
    raise DeploymentError(message=msg, error_code="deployment_error") from exc


def build_agent_payload_from_values(
    *,
    agent_name: str,
    agent_display_name: str,
    deployment_name: str,
    description: str,
    tool_ids: Sequence[str],
    llm: str,
) -> dict[str, Any]:
    # 根据给定参数构建用于 Watsonx Orchestrate 的 agent 请求体字典。
    return {
        "name": agent_name,
        "display_name": agent_display_name,
        "description": str(description).strip() or f"Langflow deployment {deployment_name}",
        "tools": list(tool_ids),
        "style": "default",
        "llm": str(llm).strip(),
    }


def extract_agent_tool_ids(agent: dict[str, Any]) -> list[str]:
    # Shape source:
    # - SDK/API agent payload uses "tools" as list[str] in this adapter flow.
    # 从 agent 字典中提取关联的 tool id 列表。
    return [str(tool_id) for tool_id in agent.get("tools", []) if tool_id]
