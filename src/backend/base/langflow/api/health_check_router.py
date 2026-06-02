import uuid

from fastapi import APIRouter, HTTPException, status
from lfx.log.logger import logger
from pydantic import BaseModel
from sqlmodel import select

from langflow.api.utils import DbSession
from langflow.services.database.models.flow.model import Flow
from langflow.services.deps import get_chat_service

# 健康检查路由，标签为 "Health Check"
health_check_router = APIRouter(tags=["Health Check"])


class HealthResponse(BaseModel):
    """健康检查响应模型，包含服务状态和各组件检查结果"""

    status: str = "nok"
    chat: str = "error check the server logs"
    db: str = "error check the server logs"
    """
    Do not send exceptions and detailed error messages to the client because it might contain credentials and other
    sensitive server information.
    """

    def has_error(self) -> bool:
        """检查响应中是否存在错误（任何字段以 'error' 开头即为错误）"""
        return any(v.startswith("error") for v in self.model_dump().values())


# /health is also supported by uvicorn
# it means uvicorn's /health serves first before the langflow instance is up
# therefore it's not a reliable health check for a langflow instance
# we keep this for backward compatibility
# 注意：uvicorn 也提供 /health 端点，但 uvicorn 的 /health 会在 langflow 实例启动前就响应
# 因此它不是一个可靠的 langflow 实例健康检查，保留此端点仅为向后兼容
@health_check_router.get("/health")
async def health():
    """简单健康检查端点，仅返回 ok 状态"""
    return {"status": "ok"}


# /health_check evaluates key services
# It's a reliable health check for a langflow instance
# /health_check 会评估关键服务，是 langflow 实例的可靠健康检查
@health_check_router.get("/health_check")
async def health_check(
    session: DbSession,
) -> HealthResponse:
    """详细健康检查端点，检查数据库和聊天服务的状态"""
    response = HealthResponse()
    # use a fixed valid UUId that UUID collision is very unlikely
    # 使用固定的 UUID 值，避免 UUID 碰撞（实际上会查询不存在的 Flow）
    user_id = "da93c2bd-c857-4b10-8c8c-60988103320f"
    try:
        # Check database to query a bogus flow
        # 通过查询一个不存在的 flow 来验证数据库连接是否正常
        stmt = select(Flow).where(Flow.id == uuid.uuid4())
        (await session.exec(stmt)).first()
        response.db = "ok"
    except Exception:  # noqa: BLE001
        await logger.aexception("Error checking database")

    try:
        # 检查聊天服务的缓存读写是否正常
        chat = get_chat_service()
        await chat.set_cache("health_check", str(user_id))
        await chat.get_cache("health_check")
        response.chat = "ok"
    except Exception:  # noqa: BLE001
        await logger.aexception("Error checking chat service")

    # 如果任一服务检查失败，返回 500 错误
    if response.has_error():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.model_dump())
    # 所有检查通过，设置整体状态为 ok
    response.status = "ok"
    return response
