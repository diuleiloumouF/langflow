import asyncio
import json
import time
import traceback
import uuid
from collections.abc import AsyncIterator

from fastapi import BackgroundTasks, HTTPException, Response
from lfx.graph.graph.base import Graph
from lfx.graph.utils import log_vertex_build
from lfx.log.logger import logger
from lfx.schema.schema import InputValueRequest
from sqlmodel import select

from langflow.api.disconnect import DisconnectHandlerStreamingResponse
from langflow.api.utils import (
    CurrentActiveUser,
    EventDeliveryType,
    build_graph_from_data,
    build_graph_from_db,
    format_elapsed_time,
    format_exception_message,
    get_top_level_vertices,
    parse_exception,
)
from langflow.api.v1.schemas import FlowDataRequest, ResultDataResponse, VertexBuildResponse
from langflow.events.event_manager import EventManager
from langflow.exceptions.component import ComponentBuildError
from langflow.schema.message import ErrorMessage
from langflow.schema.schema import OutputValue
from langflow.services.database.models.flow.model import Flow
from langflow.services.deps import get_chat_service, get_telemetry_service, session_scope
from langflow.services.job_queue.service import JobQueueNotFoundError, JobQueueService
from langflow.services.telemetry.schema import ComponentInputsPayload, ComponentPayload, PlaygroundPayload


def _log_component_input_telemetry(
    vertex,
    vertex_id: str,
    component_run_id: str,
    background_tasks: BackgroundTasks,
    telemetry_service,
) -> None:
    """Log component input telemetry if available."""
    """如果可用，记录组件输入遥测数据。"""
    if hasattr(vertex, "custom_component") and vertex.custom_component:
        inputs_dict = vertex.custom_component.get_telemetry_input_values()
        if inputs_dict:
            background_tasks.add_task(
                telemetry_service.log_package_component_inputs,
                ComponentInputsPayload(
                    component_run_id=component_run_id,
                    component_id=vertex_id,
                    component_name=vertex_id.split("-")[0],
                    component_inputs=inputs_dict,
                ),
            )


async def start_flow_build(
    *,
    flow_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    inputs: InputValueRequest | None,
    data: FlowDataRequest | None,
    files: list[str] | None,
    stop_component_id: str | None,
    start_component_id: str | None,
    log_builds: bool,
    current_user: CurrentActiveUser,
    queue_service: JobQueueService,
    flow_name: str | None = None,
    source_flow_id: uuid.UUID | None = None,
) -> str:
    """Start the flow build process by setting up the queue and starting the build task.

    Args:
        flow_id: The flow ID used for tracking, sessions, and messages.
        background_tasks: FastAPI background tasks for async operations.
        inputs: Optional input values for the flow.
        data: Optional flow data request.
        files: Optional list of file paths.
        stop_component_id: Optional component ID to stop at.
        start_component_id: Optional component ID to start from.
        log_builds: Whether to log build events.
        current_user: The currently authenticated user.
        queue_service: The job queue service instance.
        flow_name: Optional flow name override.
        source_flow_id: If provided, the actual flow ID to load from DB.
            Used by public flows where flow_id is a virtual UUID for session isolation
            but the flow data must be loaded from the original flow in the database.

    Returns:
        the job_id.
    """
    """启动流程构建任务，设置任务队列并开始构建。

    Args:
        flow_id: 流程 ID，用于追踪、会话和消息。
        background_tasks: FastAPI 后台任务，用于异步操作。
        inputs: 流程的可选输入值。
        data: 可选的流程数据请求。
        files: 可选的文件路径列表。
        stop_component_id: 可选的停止组件 ID。
        start_component_id: 可选的起始组件 ID。
        log_builds: 是否记录构建事件。
        current_user: 当前已认证的用户。
        queue_service: 任务队列服务实例。
        flow_name: 可选的流程名称覆盖。
        source_flow_id: 如果提供，为实际从数据库加载的流程 ID。
            用于公共流程，其中 flow_id 是用于会话隔离的虚拟 UUID，
            但流程数据必须从数据库中的原始流程加载。

    Returns:
        任务 ID。
    """
    job_id = str(uuid.uuid4())
    try:
        _, event_manager = queue_service.create_queue(job_id)
        task_coro = generate_flow_events(
            flow_id=flow_id,
            background_tasks=background_tasks,
            event_manager=event_manager,
            inputs=inputs,
            data=data,
            files=files,
            stop_component_id=stop_component_id,
            start_component_id=start_component_id,
            log_builds=log_builds,
            current_user=current_user,
            flow_name=flow_name,
            source_flow_id=source_flow_id,
        )
        queue_service.start_job(job_id, task_coro)
    except Exception as e:
        await logger.aexception("Failed to create queue and start task")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return job_id


async def get_flow_events_response(
    *,
    job_id: str,
    queue_service: JobQueueService,
    event_delivery: EventDeliveryType,
):
    """Get events for a specific build job, either as a stream or single event."""
    """获取特定构建任务的事件，支持流式或单次事件模式。"""
    try:
        main_queue, event_manager, event_task, _ = queue_service.get_queue_data(job_id)
        if event_delivery in (EventDeliveryType.STREAMING, EventDeliveryType.DIRECT):
            if event_task is None:
                await logger.aerror(f"No event task found for job {job_id}")
                raise HTTPException(status_code=404, detail="No event task found for job")
            return await create_flow_response(
                queue=main_queue,
                event_manager=event_manager,
                event_task=event_task,
            )

        # Polling mode - get all available events
        # 轮询模式 - 获取所有可用事件
        try:
            events: list = []
            # Get all available events from the queue without blocking
            # 从队列中获取所有可用事件，不阻塞
            while not main_queue.empty():
                _, value, _ = await main_queue.get()
                if value is None:
                    # End of stream, trigger end event
                    # 流结束，触发结束事件
                    if event_task is not None:
                        event_task.cancel()
                    event_manager.on_end(data={})
                    # Include the end event
                    # 包含结束事件
                    events.append(None)
                    break
                events.append(value.decode("utf-8"))

            # If no events were available, wait for one (with timeout)
            # 如果没有可用事件，等待一个（带超时）
            if not events:
                _, value, _ = await main_queue.get()
                if value is None:
                    # End of stream, trigger end event
                    # 流结束，触发结束事件
                    if event_task is not None:
                        event_task.cancel()
                    event_manager.on_end(data={})
                else:
                    events.append(value.decode("utf-8"))

            # Return as NDJSON format - each line is a complete JSON object
            # 以 NDJSON 格式返回 - 每行是一个完整的 JSON 对象
            content = "\n".join([event for event in events if event is not None])
            return Response(content=content, media_type="application/x-ndjson")
        except asyncio.CancelledError as exc:
            await logger.ainfo(f"Event polling was cancelled for job {job_id}")
            raise HTTPException(status_code=499, detail="Event polling was cancelled") from exc
        except asyncio.TimeoutError:
            await logger.awarning(f"Timeout while waiting for events for job {job_id}")
            return Response(content="", media_type="application/x-ndjson")  # Return empty response instead of error
            # 返回空响应而非错误

    except JobQueueNotFoundError as exc:
        await logger.aerror(f"Job not found: {job_id}. Error: {exc!s}")
        raise HTTPException(status_code=404, detail=f"Job not found: {exc!s}") from exc
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        await logger.aexception(f"Unexpected error processing flow events for job {job_id}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc!s}") from exc


async def create_flow_response(
    queue: asyncio.Queue,
    event_manager: EventManager,
    event_task: asyncio.Task,
) -> DisconnectHandlerStreamingResponse:
    """Create a streaming response for the flow build process."""
    """为流程构建过程创建流式响应。"""

    async def consume_and_yield() -> AsyncIterator[str]:
        while True:
            try:
                event_id, value, put_time = await queue.get()
                if value is None:
                    break
                get_time = time.time()
                yield value.decode("utf-8")
                await logger.adebug(f"Event {event_id} consumed in {get_time - put_time:.4f}s")
            except Exception as exc:  # noqa: BLE001
                await logger.aexception(f"Error consuming event: {exc}")
                break

    def on_disconnect() -> None:
        """客户端断开连接时的回调函数。"""
        logger.debug("Client disconnected, closing tasks")
        event_task.cancel()
        event_manager.on_end(data={})

    return DisconnectHandlerStreamingResponse(
        consume_and_yield(),
        media_type="application/x-ndjson",
        on_disconnect=on_disconnect,
    )


async def generate_flow_events(
    *,
    flow_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    event_manager: EventManager,
    inputs: InputValueRequest | None,
    data: FlowDataRequest | None,
    files: list[str] | None,
    stop_component_id: str | None,
    start_component_id: str | None,
    log_builds: bool,
    current_user: CurrentActiveUser,
    flow_name: str | None = None,
    source_flow_id: uuid.UUID | None = None,
) -> None:
    """Generate events for flow building process.

    This function handles the core flow building logic and generates appropriate events:
    - Building and validating the graph
    - Processing vertices
    - Handling errors and cleanup
    """
    """生成流程构建过程的事件。

    此函数处理核心流程构建逻辑并生成相应事件：
    - 构建和验证图
    - 处理顶点
    - 处理错误和清理
    """
    # 获取聊天服务和遥测服务实例
    chat_service = get_chat_service()
    telemetry_service = get_telemetry_service()
    if not inputs:
        inputs = InputValueRequest(session=str(flow_id))

    async def build_graph_and_get_order() -> tuple[list[str], list[str], Graph]:
        """构建图并获取顶点执行顺序。"""
        start_time = time.perf_counter()
        components_count = 0
        graph = None
        run_id = str(uuid.uuid4())
        try:
            flow_id_str = str(flow_id)
            # Create a fresh session for database operations
            # 为数据库操作创建新的会话
            async with session_scope() as fresh_session:
                graph = await create_graph(fresh_session, flow_id_str, flow_name)

            graph.set_run_id(run_id)
            first_layer = sort_vertices(graph)

            for vertex_id in first_layer:
                graph.run_manager.add_to_vertices_being_run(vertex_id)

            # Now vertices is a list of lists
            # We need to get the id of each vertex
            # and return the same structure but only with the ids
            # 现在 vertices 是一个列表的列表，需要获取每个顶点的 ID 并返回相同的结构但只包含 ID
            components_count = len(graph.vertices)
            vertices_to_run = list(graph.vertices_to_run.union(get_top_level_vertices(graph, graph.vertices_to_run)))

            await chat_service.set_cache(flow_id_str, graph)
            await log_telemetry(start_time, components_count, run_id=run_id, success=True)

        except Exception as exc:
            await log_telemetry(start_time, components_count, run_id=run_id, success=False, error_message=str(exc))

            if "stream or streaming set to True" in str(exc):
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            await logger.aexception("Error checking build status: " + str(exc))
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return first_layer, vertices_to_run, graph

    async def log_telemetry(
        start_time: float,
        components_count: int,
        *,
        run_id: str | None = None,
        success: bool,
        error_message: str | None = None,
    ):
        """记录 Playground 遥测数据。"""
        background_tasks.add_task(
            telemetry_service.log_package_playground,
            PlaygroundPayload(
                playground_seconds=int(time.perf_counter() - start_time),
                playground_component_count=components_count,
                playground_success=success,
                playground_error_message=str(error_message) if error_message else "",
                playground_run_id=run_id,
            ),
        )

    async def create_graph(fresh_session, flow_id_str: str, flow_name: str | None) -> Graph:
        """根据提供的数据或从数据库加载流程图。"""
        if inputs is not None and getattr(inputs, "session", None) is not None:
            effective_session_id = inputs.session
        else:
            effective_session_id = flow_id_str

        if not data:
            # For public flows, source_flow_id is the real DB ID, flow_id is virtual.
            # Load from DB using the real ID, then override graph.flow_id with virtual.
            # 对于公共流程，source_flow_id 是真实的数据库 ID，flow_id 是虚拟的。
            # 使用真实 ID 从数据库加载，然后用虚拟 ID 覆盖 graph.flow_id。
            db_flow_id = source_flow_id if source_flow_id is not None else flow_id
            graph = await build_graph_from_db(
                flow_id=db_flow_id,
                session=fresh_session,
                chat_service=chat_service,
                user_id=str(current_user.id),
                session_id=effective_session_id,
            )
            if source_flow_id is not None:
                graph.flow_id = str(flow_id)
            return graph

        if not flow_name:
            result = await fresh_session.exec(select(Flow.name).where(Flow.id == flow_id))
            flow_name = result.first()

        return await build_graph_from_data(
            flow_id=flow_id_str,
            payload=data.model_dump(),
            user_id=str(current_user.id),
            flow_name=flow_name,
            session_id=effective_session_id,
        )

    def sort_vertices(graph: Graph) -> list[str]:
        """对图中的顶点进行排序，支持指定起始和停止组件。"""
        try:
            return graph.sort_vertices(stop_component_id, start_component_id)
        except Exception:  # noqa: BLE001
            logger.exception("Error sorting vertices")
            return graph.sort_vertices()

    async def _build_vertex(vertex_id: str, graph: Graph, event_manager: EventManager) -> VertexBuildResponse:
        """构建单个顶点并返回构建结果。"""
        flow_id_str = str(flow_id)
        next_runnable_vertices = []
        top_level_vertices = []
        start_time = time.perf_counter()
        error_message = None

        try:
            vertex = graph.get_vertex(vertex_id)
            try:
                lock = chat_service.async_cache_locks[flow_id_str]
                vertex_build_result = await graph.build_vertex(
                    vertex_id=vertex_id,
                    user_id=str(current_user.id),
                    inputs_dict=inputs.model_dump() if inputs else {},
                    files=files,
                    get_cache=chat_service.get_cache,
                    set_cache=chat_service.set_cache,
                    event_manager=event_manager,
                )
                result_dict = vertex_build_result.result_dict
                params = vertex_build_result.params
                valid = vertex_build_result.valid
                artifacts = vertex_build_result.artifacts
                next_runnable_vertices = await graph.get_next_runnable_vertices(lock, vertex=vertex, cache=False)
                top_level_vertices = graph.get_top_level_vertices(next_runnable_vertices)

                result_data_response = ResultDataResponse.model_validate(result_dict, from_attributes=True)
            except Exception as exc:  # noqa: BLE001
                # 处理组件构建异常
                if isinstance(exc, ComponentBuildError):
                    params = exc.message
                    tb = exc.formatted_traceback
                else:
                    tb = traceback.format_exc()
                    await logger.aexception("Error building Component")
                    params = format_exception_message(exc)
                message = {"errorMessage": params, "stackTrace": tb}
                valid = False
                error_message = params
                # 获取第一个输出的名称作为输出标签
                output_label = vertex.outputs[0]["name"] if vertex.outputs else "output"
                outputs = {output_label: OutputValue(message=message, type="error")}
                result_data_response = ResultDataResponse(results={}, outputs=outputs)
                artifacts = {}
                background_tasks.add_task(graph.end_all_traces_in_context(error=exc))

            result_data_response.message = artifacts

            # Log the vertex build
            # 记录顶点构建日志
            if not vertex.will_stream and log_builds:
                background_tasks.add_task(
                    log_vertex_build,
                    flow_id=flow_id_str,
                    vertex_id=vertex_id,
                    valid=valid,
                    params=params,
                    data=result_data_response,
                    artifacts=artifacts,
                )
            else:
                await chat_service.set_cache(flow_id_str, graph)

            timedelta = time.perf_counter() - start_time

            duration = format_elapsed_time(timedelta)
            result_data_response.duration = duration
            result_data_response.timedelta = timedelta
            vertex.add_build_time(timedelta)
            # Capture both inactivated and conditionally excluded vertices
            # 捕获所有已停用和条件排除的顶点
            inactivated_vertices = list(graph.inactivated_vertices.union(graph.conditionally_excluded_vertices))
            graph.reset_inactivated_vertices()
            graph.reset_activated_vertices()

            # Note: Do not reset conditionally_excluded_vertices each iteration
            # This is handled by the ConditionalRouter component
            # 注意：每次迭代不要重置 conditionally_excluded_vertices，由 ConditionalRouter 组件处理

            # graph.stop_vertex tells us if the user asked
            # to stop the build of the graph at a certain vertex
            # if it is in next_vertices_ids, we need to remove other
            # vertices from next_vertices_ids
            # graph.stop_vertex 告诉我们用户是否要求在某个顶点停止构建，
            # 如果在 next_vertices_ids 中，需要从 next_vertices_ids 中移除其他顶点
            if graph.stop_vertex and graph.stop_vertex in next_runnable_vertices:
                next_runnable_vertices = [graph.stop_vertex]

            if not graph.run_manager.vertices_being_run and not next_runnable_vertices:
                background_tasks.add_task(graph.end_all_traces_in_context())

            build_response = VertexBuildResponse(
                inactivated_vertices=list(set(inactivated_vertices)),
                next_vertices_ids=list(set(next_runnable_vertices)),
                top_level_vertices=list(set(top_level_vertices)),
                valid=valid,
                params=params,
                id=vertex.id,
                data=result_data_response,
            )

            # Extract and send component input telemetry (separate payload)
            # 提取并发送组件输入遥测数据（独立负载）
            _log_component_input_telemetry(vertex, vertex_id, graph.run_id, background_tasks, telemetry_service)

            # Send component execution telemetry
            # 发送组件执行遥测数据
            background_tasks.add_task(
                telemetry_service.log_package_component,
                ComponentPayload(
                    component_name=vertex_id.split("-")[0],
                    component_id=vertex_id,
                    component_seconds=int(time.perf_counter() - start_time),
                    component_success=valid,
                    component_error_message=error_message,
                    component_run_id=graph.run_id,
                ),
            )
        except Exception as exc:
            if "vertex" in locals():
                # Extract and send component input telemetry even on error (separate payload)
                # 即使出错也提取并发送组件输入遥测数据（独立负载）
                _log_component_input_telemetry(vertex, vertex_id, graph.run_id, background_tasks, telemetry_service)

            # Send component execution telemetry (error case)
            # 发送组件执行遥测数据（错误情况）
            background_tasks.add_task(
                telemetry_service.log_package_component,
                ComponentPayload(
                    component_name=vertex_id.split("-")[0],
                    component_id=vertex_id,
                    component_seconds=int(time.perf_counter() - start_time),
                    component_success=False,
                    component_error_message=str(exc),
                    component_run_id=graph.run_id,
                ),
            )
            await logger.aexception("Error building Component")
            message = parse_exception(exc)
            raise HTTPException(status_code=500, detail=message) from exc

        return build_response

    async def build_vertices(
        vertex_id: str,
        graph: Graph,
        event_manager: EventManager,
        vertex_timedeltas: list[float],
    ) -> None:
        """Build vertices and handle their events.

        Args:
            vertex_id: The ID of the vertex to build
            graph: The graph instance
            event_manager: Manager for handling events
            vertex_timedeltas: Shared list to accumulate each vertex's timedelta
        """
        """构建顶点并处理其事件。

        Args:
            vertex_id: 要构建的顶点 ID
            graph: 图实例
            event_manager: 事件管理器
            vertex_timedeltas: 用于累积每个顶点耗时的共享列表
        """
        try:
            vertex_build_response: VertexBuildResponse = await _build_vertex(vertex_id, graph, event_manager)
        except asyncio.CancelledError as exc:
            await logger.ainfo(f"Build cancelled: {exc}")
            raise

        # Accumulate the vertex timedelta
        # 累积顶点耗时
        if vertex_build_response.data.timedelta is not None:
            vertex_timedeltas.append(vertex_build_response.data.timedelta)

        # send built event or error event
        # 发送构建完成事件或错误事件
        try:
            vertex_build_response_json = vertex_build_response.model_dump_json()
            build_data = json.loads(vertex_build_response_json)
        except Exception as exc:
            msg = f"Error serializing vertex build response: {exc}"
            raise ValueError(msg) from exc

        event_manager.on_end_vertex(data={"build_data": build_data})

        # 如果顶点构建成功且有后续可运行的顶点，则递归构建后续顶点
        if vertex_build_response.valid and vertex_build_response.next_vertices_ids:
            tasks = []
            for next_vertex_id in vertex_build_response.next_vertices_ids:
                task = asyncio.create_task(
                    build_vertices(
                        next_vertex_id,
                        graph,
                        event_manager,
                        vertex_timedeltas,
                    )
                )
                tasks.append(task)
            await asyncio.gather(*tasks)

    try:
        ids, vertices_to_run, graph = await build_graph_and_get_order()
    except Exception as e:
        error_message = ErrorMessage(
            flow_id=flow_id,
            exception=e,
            session_id=inputs.session,
        )
        event_manager.on_error(data=error_message.data)
        raise

    event_manager.on_vertices_sorted(data={"ids": ids, "to_run": vertices_to_run})

    vertex_timedeltas: list[float] = []
    event_manager.on_build_start(data={})
    tasks = []
    for vertex_id in ids:
        task = asyncio.create_task(build_vertices(vertex_id, graph, event_manager, vertex_timedeltas))
        tasks.append(task)
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        background_tasks.add_task(graph.end_all_traces_in_context())
        raise
    except Exception as e:
        await logger.aerror(f"Error building vertices: {e}")
        custom_component = graph.get_vertex(vertex_id).custom_component
        trace_name = getattr(custom_component, "trace_name", None)
        error_message = ErrorMessage(
            flow_id=flow_id,
            exception=e,
            session_id=graph.session_id,
            trace_name=trace_name,
        )
        event_manager.on_error(data=error_message.data)
        raise

    # 计算总构建耗时并发送结束事件
    build_duration = sum(vertex_timedeltas)
    event_manager.on_end(data={"build_duration": build_duration})
    await graph.end_all_traces()
    # 向队列发送结束信号（None 值表示流结束）
    await event_manager.queue.put((None, None, time.time()))


async def cancel_flow_build(
    *,
    job_id: str,
    queue_service: JobQueueService,
) -> bool:
    """Cancel an ongoing flow build job.

    Args:
        job_id: The unique identifier of the job to cancel
        queue_service: The service managing job queues

    Returns:
        True if the job was successfully canceled or doesn't need cancellation
        False if the cancellation failed

    Raises:
        ValueError: If the job doesn't exist
        asyncio.CancelledError: If the task cancellation failed
    """
    """取消正在进行的流程构建任务。

    Args:
        job_id: 要取消的任务唯一标识符
        queue_service: 管理任务队列的服务

    Returns:
        如果任务成功取消或无需取消则返回 True，取消失败则返回 False

    Raises:
        ValueError: 如果任务不存在
        asyncio.CancelledError: 如果任务取消失败
    """
    # Get the event task and event manager for the job
    # 获取任务的事件任务和事件管理器
    _, _, event_task, _ = queue_service.get_queue_data(job_id)

    if event_task is None:
        await logger.awarning(f"No event task found for job_id {job_id}")
        return True  # Nothing to cancel is still a success
        # 没有需要取消的内容也视为成功

    if event_task.done():
        await logger.ainfo(f"Task for job_id {job_id} is already completed")
        return True  # Nothing to cancel is still a success
        # 没有需要取消的内容也视为成功

    # Store the task reference to check status after cleanup
    # 保存任务引用以便在清理后检查状态
    task_before_cleanup = event_task

    try:
        # Perform cleanup using the queue service
        # 使用队列服务执行清理
        await queue_service.cleanup_job(job_id)
    except asyncio.CancelledError:
        # Check if the task was actually cancelled
        # 检查任务是否真的被取消了
        if task_before_cleanup.cancelled():
            await logger.ainfo(f"Successfully cancelled flow build for job_id {job_id} (CancelledError caught)")
            return True
        # If the task wasn't cancelled, re-raise the exception
        # 如果任务没有被取消，重新抛出异常
        await logger.aerror(f"CancelledError caught but task for job_id {job_id} was not cancelled")
        raise

    # If no exception was raised, verify that the task was actually cancelled
    # The task should be done (cancelled) after cleanup
    # 如果没有抛出异常，验证任务是否真的被取消了，清理后任务应该已完成（已取消）
    if task_before_cleanup.cancelled():
        await logger.ainfo(f"Successfully cancelled flow build for job_id {job_id}")
        return True

    # If we get here, the task wasn't cancelled properly
    # 如果执行到这里，说明任务没有被正确取消
    await logger.aerror(f"Failed to cancel flow build for job_id {job_id}, task is still running")
    return False
