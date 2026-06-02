# 用户辅助模块，提供根据流程 ID 或端点名称查找用户的功能
from uuid import UUID

from fastapi import HTTPException
from lfx.services.deps import session_scope_readonly
from sqlmodel import select

from langflow.services.database.models.flow.model import Flow
from langflow.services.database.models.user.model import User, UserRead


# 根据流程 ID 或端点名称异步获取对应的用户信息
# 支持传入 UUID 格式的流程 ID 或字符串格式的端点名称
async def get_user_by_flow_id_or_endpoint_name(flow_id_or_name: str) -> UserRead | None:
    # 使用只读数据库会话查询流程和用户数据
    async with session_scope_readonly() as session:
        try:
            # 尝试将输入解析为 UUID 格式的流程 ID
            flow_id = UUID(flow_id_or_name)
            # 根据流程 ID 查询流程
            flow = await session.get(Flow, flow_id)
        except ValueError:
            # 如果不是有效的 UUID，则按端点名称查询流程
            stmt = select(Flow).where(Flow.endpoint_name == flow_id_or_name)
            flow = (await session.exec(stmt)).first()

        # 流程不存在时抛出 404 错误
        if flow is None:
            raise HTTPException(status_code=404, detail=f"Flow identifier {flow_id_or_name} not found")

        # 根据流程的用户 ID 查询用户信息
        user = await session.get(User, flow.user_id)
        # 用户不存在时抛出 404 错误
        if user is None:
            raise HTTPException(status_code=404, detail=f"User for flow {flow_id_or_name} not found")

        # 将 ORM 模型转换为 Pydantic 响应模型并返回
        return UserRead.model_validate(user, from_attributes=True)
