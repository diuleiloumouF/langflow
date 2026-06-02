"""Langflow Assistant API router.

This module provides the HTTP endpoints for the Langflow Assistant.
All business logic is delegated to service modules.
"""

import uuid
from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from lfx.base.models.unified_models import (
    get_all_variables_for_provider,
    get_model_provider_variable_mapping,
    get_provider_required_variable_keys,
    get_unified_models_detailed,
)
from lfx.log.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession

from langflow.agentic.api.schemas import AssistantRequest
from langflow.agentic.services.assistant_service import (
    execute_flow_with_validation,
    execute_flow_with_validation_streaming,
)
from langflow.agentic.services.flow_executor import execute_flow_file
from langflow.agentic.services.flow_types import (
    LANGFLOW_ASSISTANT_FLOW,
    MAX_VALIDATION_RETRIES,
)
from langflow.agentic.services.provider_service import (
    PREFERRED_PROVIDERS,
    get_default_model,
    get_enabled_providers_for_user,
)
from langflow.api.utils.core import CurrentActiveUser, DbSession

# 创建 agentic 模块的 API 路由器，前缀为 /agentic，不在 OpenAPI schema 中公开
router = APIRouter(prefix="/agentic", tags=["Agentic"], include_in_schema=False)


@dataclass(frozen=True)
class _AssistantContext:
    """Resolved provider, model, and execution context for assistant endpoints."""

    # 助手端点解析后的提供者、模型和执行上下文

    # 模型提供者名称（如 OpenAI、Mistral 等）
    provider: str
    # 模型名称
    model_name: str
    # API 密钥变量名
    api_key_name: str
    # 会话标识符
    session_id: str
    # 全局变量字典，包含用户ID、流ID、模型信息等
    global_vars: dict[str, str]
    # 最大验证重试次数
    max_retries: int


# 解析助手请求所需的提供者、模型、API 密钥并构建执行上下文
async def _resolve_assistant_context(
    request: AssistantRequest,
    user_id: UUID,
    session: AsyncSession,
) -> _AssistantContext:
    """Resolve provider, model, API key, and build execution context.

    Raises:
        HTTPException: If provider is not configured or API key is missing.
    """
    # 获取模型提供者与其对应环境变量名的映射关系
    provider_variable_map = get_model_provider_variable_mapping()
    # 获取当前用户已启用的提供者列表
    enabled_providers, _ = await get_enabled_providers_for_user(user_id, session)

    # 如果没有任何提供者可用，抛出 400 错误
    if not enabled_providers:
        raise HTTPException(
            status_code=400,
            detail="No model provider is configured. Please configure at least one model provider in Settings.",
        )

    # 确定要使用的提供者：优先使用请求中指定的提供者
    provider = request.provider
    # 如果未指定提供者，则按偏好顺序选择第一个可用的提供者
    if not provider:
        for preferred in PREFERRED_PROVIDERS:
            if preferred in enabled_providers:
                provider = preferred
                break
        # 如果偏好列表中没有可用的，使用第一个可用的提供者
        if not provider:
            provider = enabled_providers[0]

    # 验证所选提供者是否在已启用列表中
    if provider not in enabled_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' is not configured. Available providers: {enabled_providers}",
        )

    # 获取提供者对应的 API 密钥变量名
    api_key_name = provider_variable_map.get(provider)
    if not api_key_name:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    # 确定模型名称：使用请求中指定的，或获取提供者的默认模型
    model_name = request.model_name or get_default_model(provider) or ""

    # 获取该提供者下所有已配置的变量
    provider_vars = get_all_variables_for_provider(user_id, provider)

    # 验证所有必需的变量是否已配置
    required_keys = get_provider_required_variable_keys(provider)
    missing_keys = [key for key in required_keys if not provider_vars.get(key)]

    # 如果缺少必需的配置项，抛出 400 错误
    if missing_keys:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Missing required configuration for {provider}: {', '.join(missing_keys)}. "
                "Please configure these in Settings > Model Providers."
            ),
        )

    # 构建全局变量字典，包含用户ID、流ID、模型名称和提供者
    global_vars: dict[str, str] = {
        "USER_ID": str(user_id),
        "FLOW_ID": request.flow_id,
        "MODEL_NAME": model_name,
        "PROVIDER": provider,
    }

    # 将提供者的所有配置变量注入到全局上下文中
    global_vars.update(provider_vars)

    # 生成会话ID：如果请求中未提供则自动生成 UUID
    session_id = request.session_id or str(uuid.uuid4())
    # 最大重试次数：使用请求中指定的值，未指定则使用默认值
    max_retries = request.max_retries if request.max_retries is not None else MAX_VALIDATION_RETRIES

    # 返回解析完成的执行上下文对象
    return _AssistantContext(
        provider=provider,
        model_name=model_name,
        api_key_name=api_key_name,
        session_id=session_id,
        global_vars=global_vars,
        max_retries=max_retries,
    )


# 执行命名流的 API 端点，从 flows 目录中加载指定流并运行
@router.post("/execute/{flow_name}")
async def execute_named_flow(flow_name: str, request: AssistantRequest, current_user: CurrentActiveUser) -> dict:
    """Execute a named flow from the flows directory."""
    user_id = current_user.id

    # 构建全局变量，包含用户ID和流ID
    global_vars = {
        "USER_ID": str(user_id),
        "FLOW_ID": request.flow_id,
    }

    # 如果请求中指定了组件ID或字段名，也添加到全局变量中
    if request.component_id:
        global_vars["COMPONENT_ID"] = request.component_id
    if request.field_name:
        global_vars["FIELD_NAME"] = request.field_name

    try:
        # 获取 OpenAI 的变量配置（某些助手功能需要）
        openai_vars = get_all_variables_for_provider(user_id, "OpenAI")
        global_vars.update(openai_vars)
    except (ValueError, HTTPException):
        logger.debug("OpenAI variables not configured, continuing without them")

    # 拼接流文件名，格式为 {flow_name}.json
    flow_filename = f"{flow_name}.json"
    # 为每次请求生成唯一的 session_id，以隔离对话记忆
    session_id = str(uuid.uuid4())

    # 执行流文件并返回结果
    return await execute_flow_file(
        flow_filename=flow_filename,
        input_value=request.input_value,
        global_variables=global_vars,
        verbose=True,
        session_id=session_id,
    )


# 检查 Langflow 助手配置状态的 API 端点
@router.get("/check-config")
async def check_assistant_config(
    current_user: CurrentActiveUser,
    session: DbSession,
) -> dict:
    """Check if the Langflow Assistant is properly configured.

    Returns available providers with their configured status and available models.
    """
    user_id = current_user.id
    # 获取用户已启用的模型提供者列表
    enabled_providers, _ = await get_enabled_providers_for_user(user_id, session)

    # 存储所有可用提供者及其模型信息
    all_providers = []

    # 如果有已启用的提供者，查询其可用的模型详情
    if enabled_providers:
        # 获取每个提供者的详细模型列表
        models_by_provider = get_unified_models_detailed(
            providers=enabled_providers,
            include_unsupported=False,
            include_deprecated=False,
            model_type="language",
        )

        # 遍历每个提供者，构建模型列表
        for provider_dict in models_by_provider:
            provider_name = provider_dict.get("provider")
            models = provider_dict.get("models", [])

            # 过滤出有效的模型（排除已废弃和不支持的模型）
            model_list = []
            for model in models:
                model_name = model.get("model_name")
                display_name = model.get("display_name", model_name)
                metadata = model.get("metadata", {})

                is_deprecated = metadata.get("deprecated", False)
                is_not_supported = metadata.get("not_supported", False)

                # 只保留未废弃且支持的模型
                if not is_deprecated and not is_not_supported:
                    model_list.append(
                        {
                            "name": model_name,
                            "display_name": display_name,
                        }
                    )

            # 获取提供者的默认模型
            default_model = get_default_model(provider_name)
            # 如果没有默认模型且有可用模型，则使用列表中的第一个
            if not default_model and model_list:
                default_model = model_list[0]["name"]

            # 只有在有可用模型时才将提供者添加到结果列表
            if model_list:
                all_providers.append(
                    {
                        "name": provider_name,
                        "configured": True,
                        "default_model": default_model,
                        "models": model_list,
                    }
                )

    # 确定默认提供者和默认模型
    default_provider = None
    default_model = None

    # 收集有可用模型的提供者名称列表
    providers_with_models = [p["name"] for p in all_providers]

    # 按偏好顺序选择默认提供者
    for preferred in PREFERRED_PROVIDERS:
        if preferred in providers_with_models:
            default_provider = preferred
            # 找到对应提供者的默认模型
            for p in all_providers:
                if p["name"] == preferred:
                    default_model = p["default_model"]
                    break
            break

    # 如果偏好列表中没有可用的，使用第一个可用的提供者
    if not default_provider and all_providers:
        default_provider = all_providers[0]["name"]
        default_model = all_providers[0]["default_model"]

    # 返回配置检查结果
    return {
        "configured": len(enabled_providers) > 0,
        "configured_providers": enabled_providers,
        "providers": all_providers,
        "default_provider": default_provider,
        "default_model": default_model,
    }


# Langflow 助手对话接口（非流式）
@router.post("/assist")
async def assist(
    request: AssistantRequest,
    current_user: CurrentActiveUser,
    session: DbSession,
) -> dict:
    """Chat with the Langflow Assistant."""
    # 解析请求上下文（包含提供者、模型、API密钥等）
    ctx = await _resolve_assistant_context(request, current_user.id, session)

    logger.info(f"Executing {LANGFLOW_ASSISTANT_FLOW} with {ctx.provider}/{ctx.model_name}")

    # 执行助手流并进行验证（支持自动重试）
    return await execute_flow_with_validation(
        flow_filename=LANGFLOW_ASSISTANT_FLOW,
        input_value=request.input_value or "",
        global_variables=ctx.global_vars,
        max_retries=ctx.max_retries,
        user_id=str(current_user.id),
        session_id=ctx.session_id,
        provider=ctx.provider,
        model_name=ctx.model_name,
        api_key_var=ctx.api_key_name,
    )


# Langflow 助手流式对话接口，支持实时推送进度更新
@router.post("/assist/stream")
async def assist_stream(
    request: AssistantRequest,
    http_request: Request,
    current_user: CurrentActiveUser,
    session: DbSession,
) -> StreamingResponse:
    """Chat with the Langflow Assistant with streaming progress updates."""
    # 解析请求上下文
    ctx = await _resolve_assistant_context(request, current_user.id, session)

    # 返回 SSE (Server-Sent Events) 流式响应
    return StreamingResponse(
        execute_flow_with_validation_streaming(
            flow_filename=LANGFLOW_ASSISTANT_FLOW,
            input_value=request.input_value or "",
            global_variables=ctx.global_vars,
            max_retries=ctx.max_retries,
            user_id=str(current_user.id),
            session_id=ctx.session_id,
            provider=ctx.provider,
            model_name=ctx.model_name,
            api_key_var=ctx.api_key_name,
            # 传递连接断开检测函数，用于在客户端断开时取消执行
            is_disconnected=http_request.is_disconnected,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
