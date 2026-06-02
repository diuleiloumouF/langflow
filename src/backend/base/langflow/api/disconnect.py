# asyncio：提供异步协程支持，用于等待和执行异步回调
import asyncio

# typing：提供类型标注支持
import typing

# StreamingResponse：FastAPI/Starlette 的流式响应基类
from fastapi.responses import StreamingResponse

# BackgroundTask：Starlette 后台任务，在响应发送完毕后执行
from starlette.background import BackgroundTask

# ContentStream：流式内容的类型定义
from starlette.responses import ContentStream

# Receive：ASGI 接收端的类型定义，用于接收客户端消息
from starlette.types import Receive


# 断开连接处理器：继承 StreamingResponse，监听客户端断开连接事件并执行回调
class DisconnectHandlerStreamingResponse(StreamingResponse):
    def __init__(
        self,
        content: ContentStream,
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
        # on_disconnect：客户端断开连接时触发的回调函数，支持同步和异步
        on_disconnect: typing.Callable | None = None,
    ):
        super().__init__(content, status_code, headers, media_type, background)
        self.on_disconnect = on_disconnect

    # 监听客户端断开连接事件，持续轮询 ASGI receive 端口直到收到断开信号
    async def listen_for_disconnect(self, receive: Receive) -> None:
        while True:
            # 从 ASGI 协议层接收消息
            message = await receive()
            # 收到 http.disconnect 消息表示客户端已断开连接
            if message["type"] == "http.disconnect":
                if self.on_disconnect:
                    # 调用断开连接回调
                    coro = self.on_disconnect()
                    # 如果回调返回的是协程对象，则 await 执行它
                    if asyncio.iscoroutine(coro):
                        await coro
                break
