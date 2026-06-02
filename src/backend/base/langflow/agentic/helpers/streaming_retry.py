"""SSE event emitters for the assistant's retry cycle.

Kept separate from the orchestration service so the retry-event composition
lives in one place and the orchestrator stays under the file-size limit.
"""
# SSE 事件发射器，用于助手的重试循环。
# 与编排服务分离保存，这样重试事件的组合逻辑集中在一个地方，
# 并且编排器的文件大小不会超限。

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from langflow.agentic.helpers.sse import format_complete_event, format_progress_event
from langflow.agentic.services.flow_types import VALIDATION_UI_DELAY_SECONDS

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


# 生成 SSE 事件的异步生成器函数
async def emit_execution_retry_events(
    *,
    attempt: int,
    total_attempts: int,
    error: str,
) -> AsyncGenerator[str, None]:
    """Yield SSE events for a flow-execution failure inside the retry loop.

    Emits a ``validation_failed`` event, waits for the UX delay, and then either:
    - emits a final ``complete`` event with ``validated=False`` if attempts are
      exhausted (so the frontend renders the "Component generation failed" card), or
    - emits a ``retrying`` event so the caller can try again with an updated prompt.

    Args:
        attempt: Zero-based index of the attempt that just failed.
        total_attempts: Total attempts allowed before giving up.
        error: User-facing friendly error message produced by extract_friendly_error.
    """
    # 为重试循环中的流程执行失败生成 SSE 事件。
    # 发送 "validation_failed" 事件，等待 UX 延迟，然后：
    # - 如果尝试次数耗尽，发送最终的 "complete" 事件（validated=False），
    #   以便前端渲染"组件生成失败"卡片；
    # - 否则发送 "retrying" 事件，让调用者使用更新后的提示重试。
    #
    # 参数：
    # attempt: 刚刚失败的尝试的零基索引。
    # total_attempts: 放弃前允许的总尝试次数。
    # error: 由 extract_friendly_error 生成的用户友好的错误消息。
    # 发送验证失败事件，包含尝试次数和错误信息
    yield format_progress_event(
        "validation_failed",
        attempt + 1,
        total_attempts,
        message="Generation failed",
        error=error,
    )
    # 等待 UX 延迟，让前端有时间显示错误状态
    await asyncio.sleep(VALIDATION_UI_DELAY_SECONDS)

    # 如果已达到最大尝试次数，发送最终失败事件并返回
    if attempt >= total_attempts - 1:
        # 发送最终完成事件，标记验证失败
        yield format_complete_event(
            {
                "result": "",
                "validated": False,
                "validation_error": error,
                "validation_attempts": attempt + 1,
            }
        )
        return

    # 发送重试事件，让调用者可以继续尝试
    yield format_progress_event(
        "retrying",
        attempt + 1,
        total_attempts,
        message="Retrying with error context...",
        error=error,
    )
    # 等待 UX 延迟，让前端有时间显示重试状态
    await asyncio.sleep(VALIDATION_UI_DELAY_SECONDS)
