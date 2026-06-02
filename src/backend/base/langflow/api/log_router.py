import asyncio
import json
from http import HTTPStatus
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from lfx.log.logger import log_buffer

from langflow.services.auth.utils import get_current_active_user

# 日志路由器，所有日志相关接口都注册在此路由器下
log_router = APIRouter(tags=["Log"])


# 发送 keepalive 信号前允许的最大未发送次数
NUMBER_OF_NOT_SENT_BEFORE_KEEPALIVE = 5


async def event_generator(request: Request):
    """SSE 事件生成器，持续从日志缓冲区读取新日志并以流式方式返回给客户端。

    通过 last_read_item 记录上次已读取的日志位置，每次循环只发送新增的日志条目。
    如果连续多次没有新日志，则发送 keepalive 信号保持连接活跃。
    """
    global log_buffer  # noqa: PLW0602
    # 上次已读取的日志条目，用于确定增量读取的起始位置
    last_read_item = None
    # 自上次 keepalive 以来未发送新日志的累计次数
    current_not_sent = 0
    # 持续监听日志，直到客户端断开连接
    while not await request.is_disconnected():
        # 本次循环需要发送的日志条目列表
        to_write: list[Any] = []
        with log_buffer.get_write_lock():
            if last_read_item is None:
                # 首次连接，从缓冲区最后一条日志开始（即获取最新的日志位置作为起点）
                last_read_item = log_buffer.buffer[len(log_buffer.buffer) - 1]
            else:
                found_last = False
                # 遍历缓冲区，找到上次已读位置之后的所有新日志
                for item in log_buffer.buffer:
                    if found_last:
                        to_write.append(item)
                        last_read_item = item
                        continue
                    if item is last_read_item:
                        found_last = True
                        continue

                # 上次已读位置的日志已不在缓冲区中（可能已被清理），则发送全部缓冲区内容
                # in case the last item is nomore in the buffer
                if not found_last:
                    for item in log_buffer.buffer:
                        to_write.append(item)
                        last_read_item = item
        if to_write:
            # 将日志以 JSON 格式逐条发送，每条日志占一行（SSE 格式）
            for ts, msg in to_write:
                yield f"{json.dumps({ts: msg})}\n\n"
        else:
            # 无新日志时，累计未发送次数
            current_not_sent += 1
            if current_not_sent == NUMBER_OF_NOT_SENT_BEFORE_KEEPALIVE:
                # 达到阈值后发送 keepalive 信号，防止连接超时断开
                current_not_sent = 0
                yield "keepalive\n\n"

        # 每秒轮询一次日志缓冲区
        await asyncio.sleep(1)


@log_router.get("/logs-stream", dependencies=[Depends(get_current_active_user)])
async def stream_logs(
    request: Request,
):
    """HTTP/2 Server-Sent-Event (SSE) endpoint for streaming logs.

    Requires authentication to prevent exposure of sensitive log data.
    It establishes a long-lived connection to the server and receives log messages in real-time.
    The client should use the header "Accept: text/event-stream".
    """
    global log_buffer  # noqa: PLW0602
    # 检查日志功能是否已启用
    if log_buffer.enabled() is False:
        raise HTTPException(
            status_code=HTTPStatus.NOT_IMPLEMENTED,
            detail="Log retrieval is disabled",
        )

    # 返回 SSE 流式响应，使用事件生成器持续推送日志
    return StreamingResponse(event_generator(request), media_type="text/event-stream")


@log_router.get("/logs", dependencies=[Depends(get_current_active_user)])
async def logs(
    lines_before: Annotated[int, Query(description="The number of logs before the timestamp or the last log")] = 0,
    lines_after: Annotated[int, Query(description="The number of logs after the timestamp")] = 0,
    timestamp: Annotated[int, Query(description="The timestamp to start getting logs from")] = 0,
):
    """Retrieve application logs with authentication required.

    SECURITY: Logs may contain sensitive information and require authentication.
    """
    global log_buffer  # noqa: PLW0602
    # 检查日志功能是否已启用
    if log_buffer.enabled() is False:
        raise HTTPException(
            status_code=HTTPStatus.NOT_IMPLEMENTED,
            detail="Log retrieval is disabled",
        )
    # 不允许同时指定 lines_before 和 lines_after，因为方向冲突
    if lines_after > 0 and lines_before > 0:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Cannot request logs before and after the timestamp",
        )
    if timestamp <= 0:
        # 未指定时间戳时的处理逻辑
        if lines_after > 0:
            # 未指定时间戳但请求时间戳之后的日志，参数不合法
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Timestamp is required when requesting logs after the timestamp",
            )
        # 返回最近 N 条日志，默认 10 条
        content = log_buffer.get_last_n(10) if lines_before <= 0 else log_buffer.get_last_n(lines_before)
    elif lines_before > 0:
        # 获取指定时间戳之前的日志
        content = log_buffer.get_before_timestamp(timestamp=timestamp, lines=lines_before)
    elif lines_after > 0:
        # 获取指定时间戳之后的日志
        content = log_buffer.get_after_timestamp(timestamp=timestamp, lines=lines_after)
    else:
        # 仅指定了时间戳，获取该时间戳之前的默认 10 条日志
        content = log_buffer.get_before_timestamp(timestamp=timestamp, lines=10)
    return JSONResponse(content=content)
