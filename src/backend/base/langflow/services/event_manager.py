"""Event Manager for Webhook Real-Time Updates.

This module provides an in-memory event broadcasting system for webhook builds.
When a UI is connected via SSE, it receives real-time build events.
"""

# Webhook 实时更新事件管理器
# 该模块为 webhook 构建提供基于内存的事件广播系统。
# 当 UI 通过 SSE 连接时，会接收实时构建事件。

from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from lfx.events.event_manager import EventManager

# 常量定义
# SSE 队列最大容量
SSE_QUEUE_MAX_SIZE = 100
# SSE 发送超时时间（秒）
SSE_EMIT_TIMEOUT_SECONDS = 1.0
# 每分钟秒数，用于时长格式化
SECONDS_PER_MINUTE = 60


class WebhookEventManager:
    """Manages SSE connections and broadcasts build events for webhooks.

    When a flow is open in the UI, it subscribes to webhook events.
    When a webhook is triggered, events are emitted to all subscribers.

    This provides the same visual experience as clicking "Play" in the UI,
    but triggered by external webhook calls.
    """

    # 管理 SSE 连接并广播 webhook 构建事件。
    # 当流程在 UI 中打开时，它会订阅 webhook 事件。
    # 当 webhook 被触发时，事件会发送给所有订阅者。
    # 这提供了与在 UI 中点击"播放"相同的可视化体验，
    # 但由外部 webhook 调用触发。

    def __init__(self) -> None:
        """Initialize the event manager with empty listeners."""
        # 初始化事件管理器，创建空的监听器集合
        # _listeners: 存储每个 flow_id 对应的监听队列集合
        self._listeners: dict[str, set[asyncio.Queue]] = defaultdict(set)
        # _vertex_start_times: 存储每个流程中顶点构建的开始时间，用于计算构建耗时
        self._vertex_start_times: dict[str, dict[str, float]] = defaultdict(dict)
        # 异步锁，确保并发操作的安全性
        self._lock = asyncio.Lock()

    def record_build_start(self, flow_id: str, vertex_id: str) -> None:
        """Record when a vertex build starts for duration calculation."""
        # 记录顶点构建开始时间，用于后续计算构建耗时
        self._vertex_start_times[flow_id][vertex_id] = time.time()

    def get_build_duration(self, flow_id: str, vertex_id: str) -> str | None:
        """Get the formatted build duration for a vertex."""
        # 获取顶点的格式化构建耗时
        start_time = self._vertex_start_times.get(flow_id, {}).get(vertex_id)
        if start_time is None:
            return None
        elapsed = time.time() - start_time
        # 清理已计算的时间记录
        self._vertex_start_times[flow_id].pop(vertex_id, None)
        return self._format_duration(elapsed)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in a human-readable way."""
        # 将秒数格式化为人类可读的时间字符串
        if seconds < 1:
            # 不到1秒，显示毫秒
            return f"{int(seconds * 1000)} ms"
        if seconds < SECONDS_PER_MINUTE:
            # 不到1分钟，显示秒
            return f"{seconds:.1f} s"
        # 超过1分钟，显示分和秒
        minutes = int(seconds // SECONDS_PER_MINUTE)
        secs = seconds % SECONDS_PER_MINUTE
        return f"{minutes}m {secs:.1f}s"

    async def subscribe(self, flow_id: str) -> asyncio.Queue:
        """Subscribe to receive events for a specific flow.

        Args:
            flow_id: The flow ID to subscribe to

        Returns:
            Queue that will receive events for this flow
        """
        # 订阅指定流程的事件
        # 创建一个新的异步队列，加入该流程的监听器集合
        queue: asyncio.Queue = asyncio.Queue(maxsize=SSE_QUEUE_MAX_SIZE)
        async with self._lock:
            self._listeners[flow_id].add(queue)
            listener_count = len(self._listeners[flow_id])

        logger.info(f"New subscriber for flow {flow_id}. Total listeners: {listener_count}")
        return queue

    async def unsubscribe(self, flow_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from flow events.

        Args:
            flow_id: The flow ID to unsubscribe from
            queue: The queue to remove
        """
        # 取消订阅流程事件
        # 从监听器集合中移除指定队列
        async with self._lock:
            if flow_id in self._listeners:
                self._listeners[flow_id].discard(queue)
                listener_count = len(self._listeners[flow_id])

                # 如果该流程没有监听者了，清理空集合
                if not self._listeners[flow_id]:
                    del self._listeners[flow_id]
                    logger.info(f"All subscribers disconnected for flow {flow_id}")
                else:
                    logger.info(f"Subscriber disconnected from flow {flow_id}. Remaining: {listener_count}")

    async def emit(self, flow_id: str, event_type: str, data: Any) -> None:
        """Emit an event to all subscribers of a flow.

        Args:
            flow_id: The flow ID to emit to
            event_type: Type of event (build_start, end_vertex, etc.)
            data: Event data (will be JSON serialized)
        """
        # 向流程的所有订阅者广播事件
        async with self._lock:
            listeners = self._listeners.get(flow_id, set()).copy()

        if not listeners:
            # 没有监听者，跳过发送（性能优化）
            return

        # 构造事件数据
        event = {
            "event": event_type,
            "data": data,
            "timestamp": time.time(),
        }

        # 发送给所有队列
        # 记录失效的队列，稍后清理
        dead_queues: set[asyncio.Queue] = set()

        for queue in listeners:
            try:
                await asyncio.wait_for(queue.put(event), timeout=SSE_EMIT_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                # 队列已满（消费者处理过慢），丢弃此事件
                logger.warning(f"Queue full for flow {flow_id}, dropping event {event_type}")
            except Exception as e:  # noqa: BLE001
                # 队列已关闭或异常，标记为待移除
                logger.error(f"Error putting event in queue for flow {flow_id}: {e}")
                dead_queues.add(queue)

        # 清理失效的队列
        if dead_queues:
            async with self._lock:
                if flow_id in self._listeners:
                    self._listeners[flow_id] -= dead_queues
                    if not self._listeners[flow_id]:
                        del self._listeners[flow_id]

    def has_listeners(self, flow_id: str) -> bool:
        """Check if there are any active listeners for a flow."""
        # 检查指定流程是否有活跃的监听者
        return flow_id in self._listeners and len(self._listeners[flow_id]) > 0


# 模块级别的单例实例（可通过依赖注入在测试中替换）
# TODO: 考虑迁移到 langflow 的服务管理器模式以获得更好的依赖注入支持
_webhook_event_manager: WebhookEventManager | None = None


def get_webhook_event_manager() -> WebhookEventManager:
    """Get the webhook event manager instance.

    Returns:
        The WebhookEventManager singleton instance.
    """
    # 获取 WebhookEventManager 的单例实例
    global _webhook_event_manager  # noqa: PLW0603
    if _webhook_event_manager is None:
        _webhook_event_manager = WebhookEventManager()
    return _webhook_event_manager


# 向后兼容的别名
webhook_event_manager = get_webhook_event_manager()


class WebhookForwardingQueue:
    """Queue adapter that forwards events to the webhook SSE.

    This class implements the queue interface expected by EventManager,
    forwarding events to connected SSE clients instead of storing them.
    """

    # 队列适配器，将事件转发到 webhook SSE。
    # 该类实现了 EventManager 期望的队列接口，
    # 将事件转发给已连接的 SSE 客户端，而不是存储它们。

    def __init__(self, flow_id: str, run_id: str | None = None):
        self.flow_id = flow_id
        self.run_id = run_id
        self._manager = get_webhook_event_manager()

    def put_nowait(self, item: tuple[str, bytes, float]) -> None:
        """Forward event to webhook SSE.

        Args:
            item: Tuple of (event_id, data_bytes, timestamp) from EventManager
        """
        # 将事件转发到 webhook SSE
        _event_id, data_bytes, _timestamp = item
        try:
            data_str = data_bytes.decode("utf-8").strip()
            if not data_str:
                return

            event_data = json.loads(data_str)
            event_type = event_data.get("event")
            event_payload = event_data.get("data", {})

            # 如果有 run_id，将其注入到事件数据中
            if self.run_id and isinstance(event_payload, dict):
                event_payload["run_id"] = self.run_id

            self._emit_async(event_type, event_payload)
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Failed to forward event to webhook SSE: flow_id={self.flow_id}, error={exc}")

    def _emit_async(self, event_type: str, event_payload: Any) -> None:
        """Emit event asynchronously (fire and forget)."""
        # 异步发送事件（发射后不管）
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(self._manager.emit(self.flow_id, event_type, event_payload))
            # 抑制 fire-and-forget 任务的异常
            task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)
        except RuntimeError:
            pass  # 没有运行中的事件循环


def create_webhook_event_manager(flow_id: str, run_id: str | None = None) -> EventManager:
    """Create an EventManager that forwards events to the webhook SSE.

    This allows webhook execution to emit real-time build events
    (end_vertex with build_data, build_start, etc.) to connected UI clients.

    Args:
        flow_id: The flow ID to emit events for
        run_id: Optional run ID to include in events

    Returns:
        EventManager configured to forward events to webhook SSE
    """
    # 创建一个将事件转发到 webhook SSE 的 EventManager
    # 这使得 webhook 执行可以向连接的 UI 客户端发送实时构建事件
    from lfx.events.event_manager import EventManager

    queue = WebhookForwardingQueue(flow_id, run_id)
    manager = EventManager(queue)

    # 注册所有标准事件类型
    manager.register_event("on_token", "token")
    manager.register_event("on_vertices_sorted", "vertices_sorted")
    manager.register_event("on_error", "error")
    manager.register_event("on_end", "end")
    manager.register_event("on_message", "add_message")
    manager.register_event("on_remove_message", "remove_message")
    manager.register_event("on_end_vertex", "end_vertex")
    manager.register_event("on_build_start", "build_start")
    manager.register_event("on_build_end", "build_end")

    return manager
