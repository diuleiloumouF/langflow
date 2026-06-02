# 服务器推送事件 (Server-Sent Events, SSE) 格式化辅助工具
"""Server-Sent Events (SSE) formatting helpers."""

import json

from langflow.agentic.api.schemas import StepType


def format_progress_event(
    step: StepType,
    attempt: int,
    max_attempts: int,
    *,
    message: str | None = None,
    error: str | None = None,
    class_name: str | None = None,
    component_code: str | None = None,
) -> str:
    """格式化 SSE 进度事件

    Format SSE progress event.

    Args:
        step: 当前处理步骤
        attempt: 当前重试次数（从 1 开始）
        max_attempts: 最大重试次数
        message: 可选的人类可读消息
        error: 可选的错误信息（用于 validation_failed 步骤）
        class_name: 可选的类名（用于 validation_failed 步骤）
        component_code: 可选的组件代码（用于 validation_failed 步骤）
    """
    # 构建进度事件的数据字典
    data: dict = {
        "event": "progress",  # 事件类型：进度
        "step": step,  # 当前步骤
        "attempt": attempt,  # 当前尝试次数
        "max_attempts": max_attempts,  # 最大尝试次数
    }
    # 仅在有值时添加可选字段，避免发送空数据
    if message:
        data["message"] = message
    if error:
        data["error"] = error
    if class_name:
        data["class_name"] = class_name
    if component_code:
        data["component_code"] = component_code
    # 按照 SSE 协议格式返回：以 "data: " 开头，JSON 编码，以两个换行符结尾
    return f"data: {json.dumps(data)}\n\n"


# 格式化 SSE 完成事件
def format_complete_event(data: dict) -> str:
    """格式化 SSE 完成事件

    Format SSE complete event.
    """
    return f"data: {json.dumps({'event': 'complete', 'data': data})}\n\n"


# 格式化 SSE 错误事件
def format_error_event(message: str) -> str:
    """格式化 SSE 错误事件

    Format SSE error event.
    """
    return f"data: {json.dumps({'event': 'error', 'message': message})}\n\n"


# 格式化 SSE token 事件，用于流式输出 LLM 生成的内容
def format_token_event(chunk: str) -> str:
    """格式化 SSE token 事件，用于流式输出 LLM 生成内容

    Format SSE token event for streaming LLM output.
    """
    return f"data: {json.dumps({'event': 'token', 'chunk': chunk})}\n\n"


# 格式化 SSE 取消事件，当客户端断开连接时触发
def format_cancelled_event() -> str:
    """格式化 SSE 取消事件，当客户端断开连接时使用

    Format SSE cancelled event when client disconnects.
    """
    return f"data: {json.dumps({'event': 'cancelled', 'message': 'Generation cancelled by user'})}\n\n"
