from __future__ import annotations

# 类型检查相关的导入，仅在静态类型检查时使用
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from fastapi import HTTPException
from lfx.log.logger import logger

# Pydantic v1 兼容层，用于创建动态模型
from pydantic.v1 import BaseModel, Field, create_model
from sqlalchemy.orm import aliased
from sqlmodel import asc, desc, select

from langflow.schema.schema import INPUT_FIELD_NAME
from langflow.services.database.models.flow.model import Flow, FlowRead
from langflow.services.deps import get_settings_service, session_scope

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from lfx.graph.graph.base import Graph
    from lfx.graph.schema import RunOutputs
    from lfx.graph.vertex.base import Vertex

from langflow.schema.data import Data

# 输入类型映射：将组件名称映射到对应的类型提示和默认值
INPUT_TYPE_MAP = {
    "ChatInput": {"type_hint": "Optional[str]", "default": '""'},
    "TextInput": {"type_hint": "Optional[str]", "default": '""'},
    "JSONInput": {"type_hint": "Optional[dict]", "default": "{}"},
}

# 排序方向分发器：将字符串排序方向映射到 SQLModel 排序函数
SORT_DISPATCHER = {
    "asc": asc,
    "desc": desc,
}


async def list_flows(*, user_id: str | None = None) -> list[Data]:
    """列出指定用户的所有流程（非组件类型）。"""
    if not user_id:
        msg = "Session is invalid"
        raise ValueError(msg)
    try:
        async with session_scope() as session:
            uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
            stmt = select(Flow).where(Flow.user_id == uuid_user_id).where(Flow.is_component == False)  # noqa: E712
            flows = (await session.exec(stmt)).all()

            return [flow.to_data() for flow in flows]
    except Exception as e:
        msg = f"Error listing flows: {e}"
        raise ValueError(msg) from e


async def list_flows_by_flow_folder(
    *,
    user_id: str | None = None,
    flow_id: str | None = None,
    order_params: dict | None = {"column": "updated_at", "direction": "desc"},  # noqa: B006
) -> list[Data]:
    """根据指定流程所在的文件夹，列出该文件夹下的所有其他流程。"""
    if not user_id:
        msg = "Session is invalid"
        raise ValueError(msg)
    if not flow_id:
        msg = "Flow ID is required"
        raise ValueError(msg)
    try:
        async with session_scope() as session:
            uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
            uuid_flow_id = UUID(flow_id) if isinstance(flow_id, str) else flow_id
            # get all flows belonging to the specified user
            # and inside the same folder as the specified flow
            # Flow 表的别名，用于关联查询获取文件夹信息
            flow_ = aliased(Flow)  # flow table alias, used to retrieve the folder
            stmt = (
                select(Flow.id, Flow.name, Flow.updated_at)
                .join(flow_, Flow.folder_id == flow_.folder_id)
                .where(flow_.id == uuid_flow_id)
                .where(flow_.user_id == uuid_user_id)
                .where(Flow.user_id == uuid_user_id)
                .where(Flow.id != uuid_flow_id)
            )
            # sort flows by the specified column and direction
            # 按照指定的列和方向对流程进行排序
            if order_params is not None:
                sort_col = getattr(Flow, order_params.get("column", "updated_at"), Flow.updated_at)
                sort_dir = SORT_DISPATCHER.get(order_params.get("direction", "desc"), desc)
                stmt = stmt.order_by(sort_dir(sort_col))

            flows = (await session.exec(stmt)).all()
            return [Data(data=dict(flow._mapping)) for flow in flows]  # noqa: SLF001
    except Exception as e:
        msg = f"Error listing flows: {e}"
        raise ValueError(msg) from e


async def list_flows_by_folder_id(
    *, user_id: str | None = None, folder_id: str | None = None, order_params: dict | None = None
) -> list[Data]:
    """根据文件夹 ID 列出该文件夹下的所有流程。"""
    if not user_id:
        msg = "Session is invalid"
        raise ValueError(msg)
    if not folder_id:
        msg = "Folder ID is required"
        raise ValueError(msg)

    if order_params is None:
        order_params = {"column": "updated_at", "direction": "desc"}

    try:
        async with session_scope() as session:
            uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
            uuid_folder_id = UUID(folder_id) if isinstance(folder_id, str) else folder_id
            stmt = (
                select(Flow.id, Flow.name, Flow.updated_at)
                .where(Flow.user_id == uuid_user_id)
                .where(Flow.folder_id == uuid_folder_id)
            )
            # 按照指定的列和方向对流程进行排序
            if order_params is not None:
                sort_col = getattr(Flow, order_params.get("column", "updated_at"), Flow.updated_at)
                sort_dir = SORT_DISPATCHER.get(order_params.get("direction", "desc"), desc)
                stmt = stmt.order_by(sort_dir(sort_col))

            flows = (await session.exec(stmt)).all()
            return [Data(data=dict(flow._mapping)) for flow in flows]  # noqa: SLF001
    except Exception as e:
        msg = f"Error listing flows: {e}"
        raise ValueError(msg) from e


async def get_flow_by_id_or_name(
    *,
    user_id: str | None = None,
    flow_id: str | None = None,
    flow_name: str | None = None,
) -> Data | None:
    """根据流程 ID 或名称获取流程数据。如果同时提供两者，优先使用 flow_id。"""
    if not user_id:
        msg = "Session is invalid"
        raise ValueError(msg)
    if not (flow_id or flow_name):
        msg = "Flow ID or Flow Name is required"
        raise ValueError(msg)

    # set user provided flow id or flow name.
    # if both are provided, flow_id is used.
    # 设置用户提供的查询属性：如果同时提供 ID 和名称，优先使用 ID
    attr, val = None, None
    if flow_name:
        attr = "name"
        val = flow_name
    if flow_id:
        attr = "id"
        val = flow_id
    if not (attr and val):
        msg = "Flow id or Name is required"
        raise ValueError(msg)
    try:
        async with session_scope() as session:
            uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id  # type: ignore[assignment]
            uuid_flow_id_or_name = val  # type: ignore[assignment]
            if isinstance(val, str) and attr == "id":
                uuid_flow_id_or_name = UUID(val)  # type: ignore[assignment]
            stmt = select(Flow).where(Flow.user_id == uuid_user_id).where(getattr(Flow, attr) == uuid_flow_id_or_name)
            flow = (await session.exec(stmt)).first()
            return flow.to_data() if flow else None

    except Exception as e:
        msg = f"Error getting flow by id: {e}"
        raise ValueError(msg) from e


async def load_flow(
    user_id: str, flow_id: str | None = None, flow_name: str | None = None, tweaks: dict | None = None
) -> Graph:
    """加载流程并返回可执行的 Graph 对象。

    支持通过 flow_id 或 flow_name 定位流程，并可应用 tweaks 修改参数。
    """
    from lfx.graph.graph.base import Graph

    from langflow.processing.process import process_tweaks

    if not flow_id and not flow_name:
        msg = "Flow ID or Flow Name is required"
        raise ValueError(msg)
    if not flow_id and flow_name:
        flow_id = await find_flow(flow_name, user_id)
        if not flow_id:
            msg = f"Flow {flow_name} not found"
            raise ValueError(msg)

    async with session_scope() as session:
        graph_data = flow.data if (flow := await session.get(Flow, flow_id)) else None
    if not graph_data:
        msg = f"Flow {flow_id} not found"
        raise ValueError(msg)
    # 如果提供了 tweaks，应用参数修改到流程数据中
    if tweaks:
        graph_data = process_tweaks(graph_data=graph_data, tweaks=tweaks)
    return Graph.from_payload(graph_data, flow_id=flow_id, user_id=user_id)


async def find_flow(flow_name: str, user_id: str) -> str | None:
    """根据流程名称和用户 ID 查找流程，返回流程 ID。"""
    async with session_scope() as session:
        uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        stmt = select(Flow).where(Flow.name == flow_name).where(Flow.user_id == uuid_user_id)
        flow = (await session.exec(stmt)).first()
        return flow.id if flow else None


async def run_flow(
    inputs: dict | list[dict] | None = None,
    tweaks: dict | None = None,
    flow_id: str | None = None,
    flow_name: str | None = None,
    output_type: str | None = "chat",
    user_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    graph: Graph | None = None,
) -> list[RunOutputs]:
    """执行流程并返回运行结果。

    支持通过 flow_id 或 flow_name 加载流程，可传入输入数据和参数调整。
    如果已提供 graph 对象则直接使用，否则根据 ID/名称加载。
    """
    if user_id is None:
        msg = "Session is invalid"
        raise ValueError(msg)
    if graph is None:
        graph = await load_flow(user_id, flow_id, flow_name, tweaks)
    if run_id:
        graph.set_run_id(UUID(run_id))
    if session_id:
        graph.session_id = session_id
    if user_id:
        graph.user_id = user_id

    if inputs is None:
        inputs = []
    if isinstance(inputs, dict):
        inputs = [inputs]

    # 将输入数据拆分为值列表、组件列表和类型列表
    inputs_list = []
    inputs_components = []
    types = []
    for input_dict in inputs:
        inputs_list.append({INPUT_FIELD_NAME: cast("str", input_dict.get("input_value"))})
        inputs_components.append(input_dict.get("components", []))
        types.append(input_dict.get("type", "chat"))

    # 根据 output_type 筛选需要输出的顶点 ID
    outputs = [
        vertex.id
        for vertex in graph.vertices
        if output_type == "debug"
        or (
            vertex.is_output and (output_type == "any" or output_type in vertex.id.lower())  # type: ignore[operator]
        )
    ]

    fallback_to_env_vars = get_settings_service().settings.fallback_to_env_var

    return await graph.arun(
        inputs_list,
        outputs=outputs,
        inputs_components=inputs_components,
        types=types,
        fallback_to_env_vars=fallback_to_env_vars,
    )


def generate_function_for_flow(
    inputs: list[Vertex], flow_id: str, user_id: str | UUID | None
) -> Callable[..., Awaitable[Any]]:
    """Generate a dynamic flow function based on the given inputs and flow ID.

    Args:
        inputs (List[Vertex]): The list of input vertices for the flow.
        flow_id (str): The ID of the flow.
        user_id (str | UUID | None): The user ID associated with the flow.

    Returns:
        Coroutine: The dynamic flow function.

    Raises:
        None

    Example:
        inputs = [vertex1, vertex2]
        flow_id = "my_flow"
        function = generate_function_for_flow(inputs, flow_id)
        result = function(input1, input2)
    """
    # 根据输入顶点生成函数参数定义，包含类型提示和默认值
    # Prepare function arguments with type hints and default values
    args = [
        (
            f"{input_.display_name.lower().replace(' ', '_')}: {INPUT_TYPE_MAP[input_.base_name]['type_hint']} = "
            f"{INPUT_TYPE_MAP[input_.base_name]['default']}"
        )
        for input_ in inputs
    ]

    # 保留原始参数名，用于构建 tweaks 字典映射
    # Maintain original argument names for constructing the tweaks dictionary
    original_arg_names = [input_.display_name for input_ in inputs]

    # 将参数列表拼接为合法的函数参数字符串
    # Prepare a Pythonic, valid function argument string
    func_args = ", ".join(args)

    # 构建原始参数名到 Python 函数参数名的映射
    # Map original argument names to their corresponding Pythonic variable names in the function
    arg_mappings = ", ".join(
        f'"{original_name}": {name}'
        for original_name, name in zip(original_arg_names, [arg.split(":")[0] for arg in args], strict=True)
    )

    # 动态生成流程执行函数的代码体
    func_body = f"""
from typing import Optional
async def flow_function({func_args}):
    tweaks = {{ {arg_mappings} }}
    from langflow.helpers.flow import run_flow
    from langchain_core.tools import ToolException
    from lfx.base.flow_processing.utils import build_data_from_result_data, format_flow_output_data
    try:
        run_outputs = await run_flow(
            tweaks={{key: {{'input_value': value}} for key, value in tweaks.items()}},
            flow_id="{flow_id}",
            user_id="{user_id}"
        )
        if not run_outputs:
                return []
        run_output = run_outputs[0]

        data = []
        if run_output is not None:
            for output in run_output.outputs:
                if output:
                    data.extend(build_data_from_result_data(output))
        return format_flow_output_data(data)
    except Exception as e:
        raise ToolException(f'Error running flow: ' + e)
"""

    # 编译并执行动态生成的函数代码
    compiled_func = compile(func_body, "<string>", "exec")
    local_scope: dict = {}
    exec(compiled_func, globals(), local_scope)  # noqa: S102
    return local_scope["flow_function"]


def build_function_and_schema(
    flow_data: Data, graph: Graph, user_id: str | UUID | None
) -> tuple[Callable[..., Awaitable[Any]], type[BaseModel]]:
    """Builds a dynamic function and schema for a given flow.

    Args:
        flow_data (Data): The flow record containing information about the flow.
        graph (Graph): The graph representing the flow.
        user_id (str): The user ID associated with the flow.

    Returns:
        Tuple[Callable, BaseModel]: A tuple containing the dynamic function and the schema.
    """
    flow_id = flow_data.id
    inputs = get_flow_inputs(graph)
    dynamic_flow_function = generate_function_for_flow(inputs, flow_id, user_id=user_id)
    schema = build_schema_from_inputs(flow_data.name, inputs)
    return dynamic_flow_function, schema


def get_flow_inputs(graph: Graph) -> list[Vertex]:
    """Retrieves the flow inputs from the given graph.

    Args:
        graph (Graph): The graph object representing the flow.

    Returns:
        List[Data]: A list of input data, where each record contains the ID, name, and description of the input vertex.
    """
    return [vertex for vertex in graph.vertices if vertex.is_input]


def build_schema_from_inputs(name: str, inputs: list[Vertex]) -> type[BaseModel]:
    """Builds a schema from the given inputs.

    Args:
        name (str): The name of the schema.
        inputs (List[tuple[str, str, str]]): A list of tuples representing the inputs.
            Each tuple contains three elements: the input name, the input type, and the input description.

    Returns:
        BaseModel: The schema model.

    """
    # 根据输入顶点动态构建 Pydantic 模型字段
    fields = {}
    for input_ in inputs:
        field_name = input_.display_name.lower().replace(" ", "_")
        description = input_.description
        fields[field_name] = (str, Field(default="", description=description))
    return create_model(name, **fields)


def get_arg_names(inputs: list[Vertex]) -> list[dict[str, str]]:
    """Returns a list of dictionaries containing the component name and its corresponding argument name.

    Args:
        inputs (List[Vertex]): A list of Vertex objects representing the inputs.

    Returns:
        List[dict[str, str]]: A list of dictionaries, where each dictionary contains the component name and its
            argument name.
    """
    return [
        {"component_name": input_.display_name, "arg_name": input_.display_name.lower().replace(" ", "_")}
        for input_ in inputs
    ]


async def get_flow_by_id_or_endpoint_name(flow_id_or_name: str, user_id: str | UUID | None = None) -> FlowRead:
    """根据流程 ID 或端点名称获取流程。

    支持通过 UUID 格式的 ID 或 endpoint_name 字符串查询。
    包含安全检查：确保只能访问当前用户拥有的流程。
    """
    async with session_scope() as session:
        # SECURITY (LE-639): previously the UUID branch below called
        # ``session.get(Flow, flow_id)`` with no ownership check, so any
        # authenticated caller could resolve any other user's flow by UUID.
        # The endpoint_name branch scoped by ``user_id`` only when a truthy
        # value was passed, so callers using this as a FastAPI ``Depends``
        # (which resolves ``user_id`` from a query param that no one sets) had
        # the same hole on both branches.  Normalize ``user_id`` once and
        # enforce it on both branches -- returning None on cross-user lookup
        # so the shared 404 below fires and we don't disclose existence of
        # another user's flow.
        # 安全修复：统一处理 user_id，在两个分支上都强制执行所有权检查
        uuid_user_id: UUID | None = None
        if user_id is not None:
            # Malformed user_id -- e.g. ``?user_id=foo`` on a legacy Depends
            # route -- previously raised a raw ValueError (500 to the client).
            # Fail closed: convert to 404 so we never disclose a flow to a
            # caller whose identity we can't resolve.
            # 格式错误的 user_id 会返回 404，避免泄露其他用户的流程信息
            try:
                uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
            except (ValueError, AttributeError) as exc:
                raise HTTPException(
                    status_code=404,
                    detail=f"Flow identifier {flow_id_or_name} not found",
                ) from exc
        try:
            # 尝试将 flow_id_or_name 解析为 UUID 进行查询
            flow_id = UUID(flow_id_or_name)
            flow = await session.get(Flow, flow_id)
            # 所有权检查：如果指定了 user_id，确保流程属于该用户
            if flow is not None and uuid_user_id is not None and flow.user_id != uuid_user_id:
                flow = None
        except ValueError:
            # 解析失败则作为 endpoint_name 字符串查询
            endpoint_name = flow_id_or_name
            stmt = select(Flow).where(Flow.endpoint_name == endpoint_name)
            if uuid_user_id is not None:
                stmt = stmt.where(Flow.user_id == uuid_user_id)
            flow = (await session.exec(stmt)).first()
        if flow is None:
            raise HTTPException(status_code=404, detail=f"Flow identifier {flow_id_or_name} not found")
        return FlowRead.model_validate(flow, from_attributes=True)


async def generate_unique_flow_name(flow_name, user_id, session):
    """生成唯一的流程名称。如果名称已存在，自动追加数字后缀如 (1)、(2) 等。"""
    original_name = flow_name
    n = 1
    while True:
        # Check if a flow with the given name exists
        # 检查是否已存在同名流程
        existing_flow = (
            await session.exec(
                select(Flow).where(
                    Flow.name == flow_name,
                    Flow.user_id == user_id,
                )
            )
        ).first()

        # If no flow with the given name exists, return the name
        # 如果不存在同名流程，直接返回当前名称
        if not existing_flow:
            return flow_name

        # If a flow with the name already exists, append (n) to the name and increment n
        # 名称已存在，追加数字后缀并继续检查
        flow_name = f"{original_name} ({n})"
        n += 1


def json_schema_from_flow(flow: Flow) -> dict:
    """Generate JSON schema from flow input nodes."""
    from lfx.graph.graph.base import Graph

    # Get the flow's data which contains the nodes and their configurations
    # 获取流程数据，包含节点及其配置信息
    flow_data = flow.data or {}

    graph = Graph.from_payload(flow_data)
    input_nodes = [vertex for vertex in graph.vertices if vertex.is_input]

    properties = {}
    required = []
    for node in input_nodes:
        node_data = node.data["node"]
        template = node_data["template"]

        for field_name, field_data in template.items():
            if isinstance(field_data, dict) and field_data.get("show", False) and not field_data.get("advanced", False):
                field_type = field_data.get("type", "string")
                properties[field_name] = {
                    "type": field_type,
                    "description": field_data.get("info", f"Input for {field_name}"),
                }
                # Update field_type in properties after determining the JSON Schema type
                # 将内部类型映射为 JSON Schema 标准类型
                if field_type == "str":
                    field_type = "string"
                elif field_type == "int":
                    field_type = "integer"
                elif field_type == "float":
                    field_type = "number"
                elif field_type == "bool":
                    field_type = "boolean"
                else:
                    logger.warning(f"Unknown field type: {field_type} defaulting to string")
                    field_type = "string"
                properties[field_name]["type"] = field_type

                if field_data.get("required", False):
                    required.append(field_name)

    return {"type": "object", "properties": properties, "required": required}
