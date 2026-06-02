"""Test OpenAI Responses Error Handling."""
# 测试 OpenAI 响应错误处理

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langflow.main import create_app


@pytest.fixture
def client():
    """创建测试客户端的固定装置。"""
    # 创建 FastAPI 应用并返回测试客户端
    app = create_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_openai_response_stream_error_handling(client):
    """Test that errors during streaming are correctly propagated to the client.

    Ensure errors are propagated as OpenAI-compatible error responses.
    """
    # Mock api_key_security dependency（模拟 api_key_security 依赖）
    # 测试流式处理期间的错误是否正确传播给客户端
    from langflow.services.auth.utils import api_key_security
    from langflow.services.database.models.user.model import UserRead

    # 模拟 API 密钥安全验证函数
    async def mock_api_key_security():
        # 获取当前 UTC 时间
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        return UserRead(
            id="00000000-0000-0000-0000-000000000000",
            username="testuser",
            is_active=True,
            is_superuser=False,
            create_at=now,
            updated_at=now,
            profile_image=None,
            store_api_key=None,
            last_login_at=None,
            optins=None,
        )

    # 覆盖应用的依赖注入
    client.app.dependency_overrides[api_key_security] = mock_api_key_security

    # Mock the flow execution to simulate an error during streaming（模拟流程执行以在流式处理期间模拟错误）
    # 模拟流程执行以在流式处理期间模拟错误
    with (
        patch("langflow.api.v1.openai_responses.get_flow_by_id_or_endpoint_name") as mock_get_flow,
        patch("langflow.api.v1.openai_responses.run_flow_generator") as _,
        patch("langflow.api.v1.openai_responses.consume_and_yield") as mock_consume,
    ):
        # Setup mock flow（设置模拟流程）
        # 创建模拟流程对象
        mock_flow = MagicMock()
        mock_flow.data = {"nodes": [{"data": {"type": "ChatInput"}}, {"data": {"type": "ChatOutput"}}]}
        mock_get_flow.return_value = mock_flow

        # We need to simulate the event manager queue behavior（我们需要模拟事件管理器队列行为）
        # The run_flow_generator in the actual code puts events into the event_manager
        # which puts them into the queue.

        # Instead of mocking the complex event manager interaction, we can mock
        # consume_and_yield to yield our simulated error event
        # 我们可以模拟 consume_and_yield 来产生模拟错误事件，而不是模拟复杂的事件管理器交互

        # Simulate an error event from the queue（模拟来自队列的错误事件）
        # 创建模拟错误事件
        error_event = json.dumps({"event": "error", "data": {"error": "Simulated streaming error"}}).encode("utf-8")

        # Yield error event then None to end stream（产生错误事件，然后产生 None 以结束流）
        async def event_generator(*_, **__):
            yield error_event
            yield None

        # 设置模拟消费函数的副作用
        mock_consume.side_effect = event_generator

        # Make the request（发送请求）
        # 发送 POST 请求
        response = client.post(
            "/api/v1/responses",
            json={"model": "test-flow-id", "input": "test input", "stream": True},
            headers={"Authorization": "Bearer test-key"},
        )

        # Check response（检查响应）
        # 验证响应状态码
        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Verify we got the error event in the stream（验证我们在流中获得了错误事件）
        # 验证我们获得了错误事件
        assert (
            "event: error" not in content
        )  # OpenAI format doesn't use event: error for the data payload itself usually, but let's check the data
        # OpenAI 格式通常不使用 event: error 来处理数据负载本身，但让我们检查数据

        # We expect a data line with the error JSON（我们期望一个包含错误 JSON 的数据行）
        # The fix implementation: yield f"data: {json.dumps(error_response)}\n\n"
        # 修复实现：产生包含错误响应的数据行

        # 验证错误消息内容
        expected_error_part = '"message": "Simulated streaming error"'
        # 验证错误消息和错误类型
        assert expected_error_part in content
        assert '"type": "processing_error"' in content

    # Clean up overrides（清理覆盖）
    # 清理依赖注入覆盖
    client.app.dependency_overrides = {}
