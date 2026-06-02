# 基础 API 路由配置
# Router for base api
from fastapi import APIRouter
from lfx.services.settings.feature_flags import FEATURE_FLAGS

# 导入 v1 版本的所有子路由
from langflow.api.v1 import (
    api_key_router,  # API 密钥管理路由
    chat_router,  # 聊天功能路由
    endpoints_router,  # 端点管理路由
    files_router,  # 文件管理路由
    flow_events_router,  # 流程事件路由
    flow_version_router,  # 流程版本管理路由
    flows_router,  # 流程管理路由
    folders_router,  # 文件夹管理路由
    knowledge_bases_router,  # 知识库管理路由
    login_router,  # 登录认证路由
    mcp_projects_router,  # MCP 项目管理路由
    mcp_router,  # MCP 协议路由
    model_options_router,  # 模型选项路由
    models_router,  # 模型管理路由
    monitor_router,  # 监控路由
    openai_responses_router,  # OpenAI 响应路由
    projects_router,  # 项目管理路由
    starter_projects_router,  # 示例项目路由
    store_router,  # 应用商店路由
    traces_router,  # 链路追踪路由
    users_router,  # 用户管理路由
    validate_router,  # 数据校验路由
    variables_router,  # 变量管理路由
)

# 导入语音模式路由
from langflow.api.v1.voice_mode import router as voice_mode_router

# 导入 v2 版本的子路由
from langflow.api.v2 import files_router as files_router_v2
from langflow.api.v2 import mcp_router as mcp_router_v2
from langflow.api.v2 import registration_router as registration_router_v2
from langflow.api.v2 import workflow_router as workflow_router_v2

# v1 版本路由组，前缀为 /v1
router_v1 = APIRouter(
    prefix="/v1",
)

# v2 版本路由组，前缀为 /v2
router_v2 = APIRouter(
    prefix="/v2",
)


def include_deployment_router(target_router: APIRouter) -> None:
    # 仅在部署功能启用时挂载部署相关路由
    """Mount deployment routes only when the deployments feature is enabled."""
    if FEATURE_FLAGS.wxo_deployments:
        from langflow.api.v1.deployments import router as deployment_router

        target_router.include_router(deployment_router)


# ==================== v1 路由注册 ====================

# 聊天功能
router_v1.include_router(chat_router)
# API 端点管理
router_v1.include_router(endpoints_router)
# 数据校验
router_v1.include_router(validate_router)
# 应用商店
router_v1.include_router(store_router)
# 流程管理
router_v1.include_router(flows_router)
# 流程事件处理
router_v1.include_router(flow_events_router)
# 流程版本控制
router_v1.include_router(flow_version_router)
# 用户管理
router_v1.include_router(users_router)
# API 密钥管理
router_v1.include_router(api_key_router)
# 登录认证
router_v1.include_router(login_router)
# 变量管理
router_v1.include_router(variables_router)
# 文件管理
router_v1.include_router(files_router)
# 运行监控
router_v1.include_router(monitor_router)
# 链路追踪
router_v1.include_router(traces_router)
# 文件夹管理
router_v1.include_router(folders_router)
# 项目管理
router_v1.include_router(projects_router)
# 示例项目
router_v1.include_router(starter_projects_router)
# 知识库管理
router_v1.include_router(knowledge_bases_router)
# MCP 协议支持
router_v1.include_router(mcp_router)
# 语音模式
router_v1.include_router(voice_mode_router)
# MCP 项目管理
router_v1.include_router(mcp_projects_router)
# OpenAI 响应接口
router_v1.include_router(openai_responses_router)
# 模型管理
router_v1.include_router(models_router)
# 模型选项配置
router_v1.include_router(model_options_router)
# 部署路由（条件加载）
include_deployment_router(router_v1)


# 智能体流程执行 - 延迟导入以避免循环依赖
# Agentic flow execution - lazy import to avoid circular dependency
def _include_agentic_router():
    from langflow.agentic.api.router import router as agentic_router

    router_v1.include_router(agentic_router)


_include_agentic_router()

# ==================== v2 路由注册 ====================

# 文件管理（v2）
router_v2.include_router(files_router_v2)
# MCP 协议（v2）
router_v2.include_router(mcp_router_v2)
# 用户注册（v2）
router_v2.include_router(registration_router_v2)
# 工作流管理（v2）
router_v2.include_router(workflow_router_v2)

# 根路由，前缀为 /api，统一挂载 v1 和 v2 路由组
router = APIRouter(
    prefix="/api",
)
router.include_router(router_v1)
router.include_router(router_v2)
