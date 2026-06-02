from __future__ import annotations

from collections.abc import Generator
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from lfx.interface.utils import extract_input_variables_from_prompt
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.message import Message

# 数据库导入已移除 - lfx 应保持轻量级
# Database imports removed - lfx should be lightweight
from lfx.services.deps import get_settings_service

if TYPE_CHECKING:
    from lfx.graph.vertex.base import Vertex


class UnbuiltObject:
    """未构建的对象占位符类"""


class UnbuiltResult:
    """未构建结果的占位符类"""


# 枚举类型，用于表示构件（artifact）的不同数据类型
class ArtifactType(str, Enum):
    """Artifact type enumeration for different data types."""

    TEXT = "text"
    RECORD = "record"
    OBJECT = "object"
    ARRAY = "array"
    STREAM = "stream"
    UNKNOWN = "unknown"
    MESSAGE = "message"


# 验证提示词是否包含输入变量
def validate_prompt(prompt: str):
    """Validate prompt."""
    if extract_input_variables_from_prompt(prompt):
        return prompt

    return fix_prompt(prompt)


# 修复提示词：如果缺少输入变量则自动添加 {input} 占位符
def fix_prompt(prompt: str):
    """Fix prompt."""
    return prompt + " {input}"


# 将嵌套列表展平为一维列表
def flatten_list(list_of_lists: list[list | Any]) -> list:
    """Flatten list of lists."""
    new_list = []
    for item in list_of_lists:
        if isinstance(item, list):
            new_list.extend(item)
        else:
            new_list.append(item)
    return new_list


# 根据值的类型确定构件（artifact）的类型
def get_artifact_type(value, build_result) -> str:
    result = ArtifactType.UNKNOWN
    match value:
        case Data():
            result = ArtifactType.RECORD

        case str():
            result = ArtifactType.TEXT

        case dict():
            result = ArtifactType.OBJECT

        case list():
            result = ArtifactType.ARRAY

        case Message():
            result = ArtifactType.MESSAGE

    # 如果类型未知，且构建结果是生成器类型或消息文本是生成器，则视为流式输出
    if result == ArtifactType.UNKNOWN and (
        isinstance(build_result, Generator) or (isinstance(value, Message) and isinstance(value.text, Generator))
    ):
        result = ArtifactType.STREAM

    return result.value


# 对原始数据进行后处理：如果是流式类型则重置为空字符串
def post_process_raw(raw, artifact_type: str):
    if artifact_type == ArtifactType.STREAM.value:
        raw = ""

    return raw


# 将任意对象转换为 JSON 可序列化的格式
def serialize_for_json(obj: Any) -> Any:
    """Convert object to JSON-serializable format.

    Args:
        obj: Any object to serialize

    Returns:
        JSON-serializable representation of the object
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    if hasattr(obj, "model_dump"):
        return serialize_for_json(obj.model_dump())
    if hasattr(obj, "dict"):
        return serialize_for_json(obj.dict())
    try:
        return str(obj)
    except (TypeError, ValueError):
        return None


# 发送顶点构建完成事件，用于 webhook 实时反馈
async def emit_vertex_build_event(
    *,
    flow_id: str | UUID,
    vertex_id: str,
    valid: bool,
    params: Any,
    data_dict: dict | Any,
    artifacts_dict: dict | None = None,
    next_vertices_ids: list[str] | None = None,
    top_level_vertices: list[str] | None = None,
    inactivated_vertices: list[str] | None = None,
) -> None:
    """Emit end_vertex event for webhook real-time feedback.

    This is a helper function to emit SSE events when vertices are built.
    Errors are silently ignored as SSE emission is not critical.

    Args:
        flow_id: The flow ID
        vertex_id: The vertex ID that was built
        valid: Whether the build was successful
        params: Build parameters or error message
        data_dict: Build result data
        artifacts_dict: Build artifacts
        next_vertices_ids: IDs of vertices to run next (for UI animation)
        top_level_vertices: Top level vertices
        inactivated_vertices: Vertices that were inactivated
    """
    try:
        from datetime import datetime, timezone

        from langflow.services.event_manager import webhook_event_manager

        flow_id_str = str(flow_id)
        if not webhook_event_manager.has_listeners(flow_id_str):
            return

        duration = webhook_event_manager.get_build_duration(flow_id_str, vertex_id)

        # 如果 data_dict 是 Pydantic 模型则转换为字典
        # Convert Pydantic model to dict if necessary
        if hasattr(data_dict, "model_dump"):
            data_as_dict = data_dict.model_dump()
        elif isinstance(data_dict, dict):
            data_as_dict = data_dict
        else:
            data_as_dict = {}

        # 序列化各部分数据以便 JSON 编码
        results = serialize_for_json(data_as_dict.get("results", {}))
        outputs = serialize_for_json(data_as_dict.get("outputs", {}))
        logs = serialize_for_json(data_as_dict.get("logs", {}))
        messages = serialize_for_json(data_as_dict.get("messages", []))

        vertex_data = {
            "results": results,
            "outputs": outputs,
            "logs": logs,
            "messages": messages,
            "duration": duration,
        }

        serialized_artifacts = serialize_for_json(artifacts_dict) if artifacts_dict else {}

        # 通过 webhook 事件管理器发送 end_vertex 事件
        await webhook_event_manager.emit(
            flow_id_str,
            "end_vertex",
            {
                "build_data": {
                    "id": vertex_id,
                    "valid": valid,
                    "params": str(params) if params else None,
                    "data": vertex_data,
                    "artifacts": serialized_artifacts,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "messages": vertex_data.get("messages", []),
                    "inactivated_vertices": inactivated_vertices or [],
                    "next_vertices_ids": next_vertices_ids or [],
                    "top_level_vertices": top_level_vertices or [],
                }
            },
        )
    except ImportError:
        # langflow 不可用时（独立 lfx 使用场景）静默跳过
        pass  # langflow not available (standalone lfx usage)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"SSE emission failed for vertex {vertex_id}: {exc}")


# 发送顶点构建开始事件，用于 webhook 实时反馈
async def emit_build_start_event(flow_id: str | UUID, vertex_id: str) -> None:
    """Emit build_start event for webhook real-time feedback.

    This is a helper function to emit SSE events when a vertex build starts.
    Errors are silently ignored as SSE emission is not critical.
    """
    try:
        from langflow.services.event_manager import webhook_event_manager

        flow_id_str = str(flow_id)
        if not webhook_event_manager.has_listeners(flow_id_str):
            return

        # 记录构建开始时间并发送 build_start 事件
        webhook_event_manager.record_build_start(flow_id_str, vertex_id)
        await webhook_event_manager.emit(flow_id_str, "build_start", {"id": vertex_id})
    except ImportError:
        # langflow 不可用时（独立 lfx 使用场景）静默跳过
        pass  # langflow not available (standalone lfx usage)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"SSE build_start emission failed for vertex {vertex_id}: {exc}")


# 清理顶点参数，只保留基本 Python 类型的值
def _vertex_to_primitive_dict(target: Vertex) -> dict:
    """Cleans the parameters of the target vertex."""
    # 移除所有值不是 Python 基本类型（如 str、int、bool 等）的键
    # Removes all keys that the values aren't python types like str, int, bool, etc.
    params = {
        key: value for key, value in target.params.items() if isinstance(value, str | int | bool | float | list | dict)
    }
    # 如果值是列表，需要检查列表内容是否都是基本类型
    # if it is a list we need to check if the contents are python types
    for key, value in params.items():
        if isinstance(value, list):
            params[key] = [item for item in value if isinstance(item, str | int | bool | float | list | dict)]
    return params


# 异步记录顶点事务日志，如果启用了事务存储功能
async def log_transaction(
    flow_id: str | UUID,
    source: Vertex,
    status: str,
    target: Vertex | None = None,
    error: str | Exception | None = None,
    outputs: dict[str, Any] | None = None,
) -> None:
    """Asynchronously logs a transaction record for a vertex in a flow if transaction storage is enabled.

    Uses the pluggable TransactionService to log transactions. When running within langflow,
    the concrete TransactionService implementation persists to the database.
    When running standalone (lfx only), transactions are not persisted.

    Args:
        flow_id: The flow ID
        source: The source vertex (component being executed)
        status: Transaction status (success/error)
        target: Optional target vertex (for data transfer logging)
        error: Optional error information
        outputs: Optional explicit outputs dict (component execution results)
    """
    try:
        # 防止 source 为 None
        # Guard against null source
        if source is None:
            return

        # 通过依赖注入获取事务服务
        # Get the transaction service via dependency injection
        from lfx.services.deps import get_transaction_service

        transaction_service = get_transaction_service()

        # 如果没有事务服务或服务未启用，则跳过日志记录
        # If no transaction service is available or it's disabled, skip logging
        if transaction_service is None or not transaction_service.is_enabled():
            return

        # 解析 flow_id
        # Resolve flow_id
        if not flow_id:
            if source.graph.flow_id:
                flow_id = source.graph.flow_id
            else:
                return

        # 将 UUID 转换为字符串以适配服务接口
        # Convert UUID to string for the service interface
        flow_id_str = str(flow_id) if isinstance(flow_id, UUID) else flow_id

        # 准备输入和输出数据
        # Prepare inputs and outputs
        inputs = _vertex_to_primitive_dict(source) if source else None
        target_outputs = _vertex_to_primitive_dict(target) if target else None
        transaction_outputs = outputs if outputs is not None else target_outputs

        # 通过服务记录事务日志
        # Log transaction via the service
        await transaction_service.log_transaction(
            flow_id=flow_id_str,
            vertex_id=source.id,
            inputs=inputs,
            outputs=transaction_outputs,
            status=status,
            target_id=target.id if target else None,
            error=str(error) if error else None,
        )

    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Error logging transaction: {exc!s}")


# 异步记录顶点构建日志，如果启用了顶点构建存储功能
async def log_vertex_build(
    *,
    flow_id: str | UUID,
    vertex_id: str,
    valid: bool,
    params: Any,
    data: dict | Any,
    artifacts: dict | None = None,
    job_id: str | None = None,
) -> None:
    """Asynchronously logs a vertex build record if vertex build storage is enabled.

    This is a lightweight implementation that only logs if database service is available.
    When running within langflow, it will use langflow's database service to persist the build.
    When running standalone (lfx only), it will only log debug messages.
    """
    try:
        # 尝试使用 langflow 的服务（在 langflow 环境中运行时）
        # Try to use langflow's services if available (when running within langflow)
        try:
            from langflow.services.deps import get_db_service as langflow_get_db_service
            from langflow.services.deps import get_settings_service as langflow_get_settings_service

            settings_service = langflow_get_settings_service()
            if not settings_service:
                return
            # 检查是否启用了顶点构建存储
            if not getattr(settings_service.settings, "vertex_builds_storage_enabled", False):
                return

            if isinstance(flow_id, str):
                flow_id = UUID(flow_id)

            from langflow.services.database.models.vertex_builds.crud import (
                log_vertex_build as crud_log_vertex_build,
            )
            from langflow.services.database.models.vertex_builds.model import VertexBuildBase

            # 如果 data 是 Pydantic 模型则转换为字典
            # Convert data to dict if it's a pydantic model
            data_dict = data
            if hasattr(data, "model_dump"):
                data_dict = data.model_dump()
            elif hasattr(data, "dict"):
                data_dict = data.dict()

            # 如果 artifacts 是 Pydantic 模型则转换为字典
            # Convert artifacts to dict if it's a pydantic model
            artifacts_dict = artifacts
            if artifacts is not None:
                if hasattr(artifacts, "model_dump"):
                    artifacts_dict = artifacts.model_dump()
                elif hasattr(artifacts, "dict"):
                    artifacts_dict = artifacts.dict()

            # 构建顶点构建记录对象
            vertex_build = VertexBuildBase(
                flow_id=flow_id,
                id=vertex_id,
                valid=valid,
                params=str(params) if params else None,
                data=data_dict,
                artifacts=artifacts_dict,
                job_id=job_id,
            )

            db_service = langflow_get_db_service()
            if db_service is None:
                return

            # 通过数据库服务持久化顶点构建记录
            async with db_service._with_session() as session:  # noqa: SLF001
                await crud_log_vertex_build(session, vertex_build)

            # 注意：此处不调用 emit_vertex_build_event，因为它需要 next_vertices_ids，
            # 而这些 ID 只在 graph.get_next_runnable_vertices() 之后才可用。
            # 该事件在 graph._execute_tasks() 中使用完整数据单独发送。
            # Note: emit_vertex_build_event is NOT called here because it needs
            # next_vertices_ids which are only available after graph.get_next_runnable_vertices()
            # The event is emitted separately in graph._execute_tasks() with complete data.

        except ImportError:
            # 独立 lfx 使用时的回退逻辑（无 langflow 环境）
            # Fallback for standalone lfx usage (without langflow)
            settings_service = get_settings_service()
            if not settings_service or not getattr(settings_service.settings, "vertex_builds_storage_enabled", False):
                return

            if isinstance(flow_id, str):
                flow_id = UUID(flow_id)

            # 记录基本的顶点构建信息 - 具体实现在 langflow 中
            # Log basic vertex build info - concrete implementation is in langflow
            logger.debug(f"Vertex build logged: vertex={vertex_id}, flow={flow_id}, valid={valid}")

    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Error logging vertex build: {exc}")


# 重写文件路径：统一路径分隔符并提取最后两级目录
def rewrite_file_path(file_path: str):
    # 将反斜杠替换为正斜杠，统一路径格式
    file_path = file_path.replace("\\", "/")

    # 如果路径包含冒号（Windows 盘符），则去除盘符部分
    if ":" in file_path:
        file_path = file_path.split(":", 1)[-1]

    # 按斜杠分割并过滤空字符串
    file_path_split = [part for part in file_path.split("/") if part]

    # 如果路径层级大于1，取最后两级目录；否则返回完整路径
    if len(file_path_split) > 1:
        consistent_file_path = f"{file_path_split[-2]}/{file_path_split[-1]}"
    else:
        consistent_file_path = "/".join(file_path_split)

    return [consistent_file_path]


# 检查顶点集合中是否包含输出类型的顶点
def has_output_vertex(vertices: dict[Vertex, int]):
    return any(vertex.is_output for vertex in vertices)


# 检查顶点集合中是否包含聊天输出组件
def has_chat_output(vertices: dict[Vertex, int]):
    from lfx.graph.schema import InterfaceComponentTypes

    return any(vertex.base_name == InterfaceComponentTypes.ChatOutput.value for vertex in vertices)


# 检查顶点集合中是否包含聊天输入组件
def has_chat_input(vertices: dict[Vertex, int]):
    from lfx.graph.schema import InterfaceComponentTypes

    return any(vertex.base_name == InterfaceComponentTypes.ChatInput.value for vertex in vertices)
