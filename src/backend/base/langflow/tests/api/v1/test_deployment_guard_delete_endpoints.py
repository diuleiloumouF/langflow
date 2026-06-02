# 部署守卫删除端点测试模块
# 测试项目删除、流程删除和更新流程时的部署守卫错误处理
from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from langflow.api.utils import cascade_delete_flow
from langflow.api.v1.projects import delete_project
from langflow.services.database.models.deployment.exceptions import DeploymentGuardError


# 模拟数据库查询结果的辅助类
class _ExecResult:
    """模拟数据库查询结果的辅助类。"""

    def __init__(self, value):
        self._value = value

    def first(self):
        """返回第一行结果。"""
        return self._value

    def all(self):
        """返回所有结果行。"""
        return self._value


# 异步空上下文管理器，用于模拟 savepoint 事务
class _AsyncNullContext:
    """异步空上下文管理器，用于模拟数据库事务。"""

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_delete_project_raises_guard_error_from_app_level_check(monkeypatch):
    """测试删除项目时，在应用级别检查中抛出部署守卫错误。"""
    # 生成项目 ID 和用户 ID
    project_id = uuid4()
    user_id = uuid4()

    # 模拟设置服务，禁用 MCP 服务器配置
    monkeypatch.setattr(
        "langflow.api.v1.projects.get_settings_service",
        lambda: SimpleNamespace(settings=SimpleNamespace(add_projects_to_mcp_servers=False)),
    )
    # 模拟 MCP 清理函数
    monkeypatch.setattr("langflow.api.v1.projects.cleanup_mcp_on_delete", AsyncMock())
    # 模拟部署同步函数
    monkeypatch.setattr("langflow.api.v1.mappers.deployments.sync.sync_project_deployments", AsyncMock())

    # 创建模拟数据库会话
    session = AsyncMock()
    project = SimpleNamespace(id=project_id, name="Test Project", auth_settings=None)
    # 模拟数据库查询结果序列
    session.exec = AsyncMock(
        side_effect=[
            _ExecResult(project),  # initial project lookup（初始项目查询）
            _ExecResult([]),  # first attempt: flows query（第一次尝试：流程查询）
            _ExecResult(uuid4()),  # first attempt: check_project_has_deployments（第一次尝试：检查项目是否有部署）
            _ExecResult([]),  # second attempt: flows query（第二次尝试：流程查询）
            _ExecResult(uuid4()),  # second attempt: check_project_has_deployments（第二次尝试：检查项目是否有部署）
        ]
    )
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.begin_nested = lambda: _AsyncNullContext()

    with pytest.raises(
        DeploymentGuardError,
        match=(
            r"project cannot be deleted because it has deployments\. "
            r"Please delete its deployments first\."
        ),
    ):
        await delete_project(
            session=session,
            project_id=project_id,
            current_user=SimpleNamespace(id=user_id),
        )

    session.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_project_remaps_flow_guard_to_project_guard(monkeypatch):
    """测试删除项目时，将流程守卫错误重新映射为项目守卫错误。"""
    # 生成项目 ID、用户 ID 和流程 ID
    project_id = uuid4()
    user_id = uuid4()
    flow_id = uuid4()

    monkeypatch.setattr(
        "langflow.api.v1.projects.get_settings_service",
        lambda: SimpleNamespace(settings=SimpleNamespace(add_projects_to_mcp_servers=False)),
    )
    monkeypatch.setattr("langflow.api.v1.projects.cleanup_mcp_on_delete", AsyncMock())
    monkeypatch.setattr("langflow.api.v1.mappers.deployments.sync.sync_project_deployments", AsyncMock())
    monkeypatch.setattr(
        "langflow.api.v1.projects.cascade_delete_flow",
        AsyncMock(
            side_effect=DeploymentGuardError(
                code="FLOW_HAS_DEPLOYED_VERSIONS",
                technical_detail=(
                    "DELETE flow_version blocked: dependent rows exist in flow_version_deployment_attachment "
                    "for the target flow."
                ),
                detail=(
                    "This flow cannot be deleted because it has deployed versions. "
                    "Please remove its versions from deployments first."
                ),
            )
        ),
    )

    session = AsyncMock()
    project = SimpleNamespace(id=project_id, name="Test Project", auth_settings=None)
    session.exec = AsyncMock(
        side_effect=[
            _ExecResult(project),  # initial project lookup
            _ExecResult([SimpleNamespace(id=flow_id)]),  # first attempt: flows query
            _ExecResult([SimpleNamespace(id=flow_id)]),  # second attempt: flows query
        ]
    )
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.begin_nested = lambda: _AsyncNullContext()

    with pytest.raises(
        DeploymentGuardError,
        match=(
            r"project cannot be deleted because it has deployments\. "
            r"Please delete its deployments first\."
        ),
    ) as exc_info:
        await delete_project(
            session=session,
            project_id=project_id,
            current_user=SimpleNamespace(id=user_id),
        )

    assert exc_info.value.code == "PROJECT_HAS_DEPLOYMENTS"
    assert "DELETE folder blocked while deleting project flows" in exc_info.value.technical_detail
    session.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_cascade_delete_flow_raises_guard_error_from_app_level_check():
    """cascade_delete_flow should run app-level guard checks before issuing deletes."""
    # 测试级联删除流程时，在发出删除操作前运行应用级别守卫检查
    flow_id = uuid4()

    # 创建模拟数据库会话
    session = AsyncMock()
    session.exec = AsyncMock(return_value=_ExecResult(uuid4()))

    with pytest.raises(
        DeploymentGuardError,
        match=(
            r"flow cannot be deleted because it has deployed versions\. "
            r"Please remove its versions from deployments first\."
        ),
    ):
        await cascade_delete_flow(session, flow_id)
    assert session.exec.await_count == 1


@pytest.mark.asyncio
async def test_cascade_delete_flow_prunes_orphan_attachments_before_delete_statements():
    """cascade_delete_flow should remove stale attachment rows before deleting flow rows."""
    # 测试级联删除流程时，在删除流程行之前清理过时的附件行
    flow_id = uuid4()

    # 创建模拟数据库会话
    session = AsyncMock()
    # 模拟数据库查询结果序列
    session.exec = AsyncMock(
        side_effect=[
            _ExecResult(None),  # live deployment attachment lookup（实时部署附件查询）
            _ExecResult([uuid4()]),  # stale attachment lookup（过时附件查询）
            _ExecResult(None),  # stale attachment delete（过时附件删除）
            _ExecResult(None),  # message delete（消息删除）
            _ExecResult(None),  # transaction delete（事务删除）
            _ExecResult(None),  # vertex_build delete（顶点构建删除）
            _ExecResult(None),  # flow_version delete（流程版本删除）
            _ExecResult([]),  # trace id lookup（追踪 ID 查询）
            _ExecResult(None),  # flow delete（流程删除）
        ]
    )

    await cascade_delete_flow(session, flow_id)

    assert session.exec.await_count == 9


@pytest.mark.asyncio
async def test_delete_flow_remaps_guard_error_to_flow_delete_message(monkeypatch):
    """测试删除流程时，将守卫错误重新映射为流程删除消息。"""
    from langflow.api.v1.flows import delete_flow

    # 生成流程 ID 和用户 ID
    flow_id = uuid4()
    user_id = uuid4()

    # 创建模拟流程对象
    fake_flow = SimpleNamespace(id=flow_id, user_id=user_id)
    monkeypatch.setattr("langflow.api.v1.flows._read_flow", AsyncMock(return_value=fake_flow))
    monkeypatch.setattr(
        "langflow.api.v1.flows.retry_flow_operation_on_deployment_guard",
        AsyncMock(
            side_effect=DeploymentGuardError(
                code="FLOW_HAS_DEPLOYED_VERSIONS",
                technical_detail=(
                    "DELETE flow_version blocked: dependent rows exist in flow_version_deployment_attachment "
                    "for the target flow."
                ),
                detail=(
                    "This flow cannot be deleted because it has deployed versions. "
                    "Please remove its versions from deployments first."
                ),
            )
        ),
    )

    with pytest.raises(
        DeploymentGuardError,
        match=(
            r"cannot be deleted because it has deployed versions\. "
            r"Please remove its versions from deployments first\."
        ),
    ) as exc_info:
        await delete_flow(
            session=AsyncMock(),
            flow_id=flow_id,
            current_user=SimpleNamespace(id=user_id),
        )

    assert exc_info.value.code == "FLOW_HAS_DEPLOYED_VERSIONS"
    assert "DELETE flow_version blocked" in exc_info.value.technical_detail


@pytest.mark.asyncio
async def test_update_flow_translates_guard_error_from_flush(monkeypatch):
    """update_flow must propagate DeploymentGuardError from guarded operations."""
    # 测试更新流程时，必须从守卫操作中传播 DeploymentGuardError
    from langflow.api.v1.flows import update_flow
    from langflow.services.database.models.flow.model import FlowUpdate

    # 生成各种 ID
    flow_id = uuid4()
    user_id = uuid4()
    folder_id = uuid4()
    new_folder_id = uuid4()

    # 创建模拟流程对象
    fake_flow = SimpleNamespace(
        id=flow_id,
        user_id=user_id,
        folder_id=folder_id,
        data={"nodes": [], "edges": []},
        fs_path=None,
        webhook=False,
        updated_at=None,
    )

    monkeypatch.setattr("langflow.api.v1.flows._read_flow", AsyncMock(return_value=fake_flow))
    monkeypatch.setattr(
        "langflow.api.v1.flows._patch_flow",
        AsyncMock(
            side_effect=DeploymentGuardError(
                code="FLOW_DEPLOYED_IN_PROJECT",
                technical_detail=(
                    "Cannot move flow to a different project because it has versions deployed in the current project."
                ),
                detail=(
                    "This flow cannot be moved to another project until its versions "
                    "are removed from deployments in its current project."
                ),
            )
        ),
    )
    monkeypatch.setattr("langflow.api.v1.mappers.deployments.sync.sync_flow_deployment_state", AsyncMock())
    monkeypatch.setattr(
        "langflow.api.v1.flows.get_settings_service",
        lambda: SimpleNamespace(settings=SimpleNamespace(remove_api_keys=False)),
    )

    session = AsyncMock()
    session.exec = AsyncMock(return_value=_ExecResult(SimpleNamespace(id=new_folder_id)))
    session.add = AsyncMock()
    session.begin_nested = lambda: _AsyncNullContext()

    flow_update = FlowUpdate(folder_id=new_folder_id)

    with pytest.raises(
        DeploymentGuardError,
        match=(
            r"cannot be moved to another project until its versions are "
            r"removed from deployments in its current project"
        ),
    ):
        await update_flow(
            session=session,
            flow_id=flow_id,
            flow=flow_update,
            current_user=SimpleNamespace(id=user_id),
            storage_service=AsyncMock(),
        )


@pytest.mark.asyncio
async def test_delete_multiple_flows_propagates_guard_error(monkeypatch):
    """delete_multiple_flows must let DeploymentGuardError propagate to the caller."""
    # 测试批量删除流程时，必须让 DeploymentGuardError 传播给调用者
    from langflow.api.v1.flows import delete_multiple_flows

    # 生成流程 ID 和用户 ID
    flow_id = uuid4()
    user_id = uuid4()

    # 创建模拟流程对象
    fake_flow = SimpleNamespace(id=flow_id)

    monkeypatch.setattr(
        "langflow.api.v1.flows.cascade_delete_flow",
        AsyncMock(
            side_effect=DeploymentGuardError(
                code="FLOW_HAS_DEPLOYED_VERSIONS",
                technical_detail=(
                    "DELETE flow_version blocked: dependent rows exist in flow_version_deployment_attachment "
                    "for the target flow."
                ),
                detail=(
                    "This flow cannot be deleted because it has deployed versions. "
                    "Please remove its versions from deployments first."
                ),
            )
        ),
    )
    monkeypatch.setattr("langflow.api.v1.mappers.deployments.sync.sync_flow_deployment_state", AsyncMock())

    session = AsyncMock()
    session.exec = AsyncMock(return_value=_ExecResult([fake_flow]))
    session.begin_nested = lambda: _AsyncNullContext()

    with pytest.raises(
        DeploymentGuardError,
        match=(
            r"cannot be deleted because it has deployed versions\. "
            r"Please remove its versions from deployments first\."
        ),
    ):
        await delete_multiple_flows(
            flow_ids=[flow_id],
            user=SimpleNamespace(id=user_id),
            db=session,
        )


# ── Global exception handler ────────────────────────────────────────
# 全局异常处理器测试


@pytest.mark.asyncio
async def test_global_exception_handler_returns_409_for_deployment_guard_error():
    """The global exception handler must convert DeploymentGuardError to a 409 Conflict response."""
    # 测试全局异常处理器必须将 DeploymentGuardError 转换为 409 冲突响应

    async def _handler(_request, exc: Exception):
        """模拟的异常处理器。"""
        # 如果是部署守卫错误，返回 409 冲突响应
        if isinstance(exc, DeploymentGuardError):
            return JSONResponse(
                status_code=HTTPStatus.CONFLICT,
                content={"detail": exc.detail},
            )
        return JSONResponse(status_code=500, content={"message": str(exc)})

    # 创建 FastAPI 应用并注册异常处理器
    app = FastAPI()
    app.add_exception_handler(DeploymentGuardError, _handler)

    # 定义错误详情
    _detail = "Cannot delete project because it contains deployments."

    @app.get("/boom")
    async def _boom():
        """模拟抛出部署守卫错误的端点。"""
        # 抛出部署守卫错误
        raise DeploymentGuardError(
            code="PROJECT_HAS_DEPLOYMENTS",
            technical_detail="DELETE folder blocked: dependent rows exist in deployment for the target project.",
            detail=_detail,
        )

    # 使用异步 HTTP 客户端发送请求
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/boom")

    # 验证响应状态码和内容
    assert response.status_code == 409
    body = response.json()
    assert body == {"detail": _detail}
