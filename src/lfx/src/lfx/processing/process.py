"""图执行与调整处理模块。

提供图的运行、输入验证、调整(tweaks)应用等功能。
支持对图中的节点参数进行动态修改，以及将调整应用于已构建的图顶点。
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from json_repair import repair_json
from pydantic import BaseModel

from lfx.graph.vertex.base import Vertex
from lfx.log.logger import logger
from lfx.schema.graph import InputValue, Tweaks
from lfx.schema.schema import INPUT_FIELD_NAME, InputValueRequest
from lfx.services.deps import get_settings_service

if TYPE_CHECKING:
    from lfx.events.event_manager import EventManager
    from lfx.graph.graph.base import Graph
    from lfx.graph.schema import RunOutputs


def validate_and_repair_json(json_str: str | dict) -> dict[str, Any] | str:
    """Validates a JSON string and attempts to repair it if invalid.
    验证 JSON 字符串，如果无效则尝试修复。

    Args:
        json_str (str): The JSON string to validate/repair

    Returns:
        Union[Dict[str, Any], str]: The parsed JSON dict if valid/repairable,
        otherwise returns the original string
    """
    # 非字符串类型直接返回原值
    if not isinstance(json_str, str):
        return json_str
    try:
        # If invalid, attempt repair
        # 如果 JSON 无效，尝试修复
        repaired = repair_json(json_str)
        return json.loads(repaired)
    except (json.JSONDecodeError, ImportError):
        # Return original if repair fails or module not found
        # 修复失败或模块未安装时，返回原始字符串
        return json_str


class Result(BaseModel):
    """图运行结果的包装类，包含执行结果和会话 ID。"""

    result: Any
    session_id: str


async def run_graph_internal(
    graph: Graph,
    flow_id: str,
    *,
    stream: bool = False,
    session_id: str | None = None,
    inputs: list[InputValueRequest] | None = None,
    outputs: list[str] | None = None,
    event_manager: EventManager | None = None,
) -> tuple[list[RunOutputs], str]:
    """Run the graph and generate the result.
    内部执行图并生成结果，供 API 路由层调用。
    """
    # 默认使用空列表，避免 None 引用
    inputs = inputs or []
    # 优先使用传入的 session_id，否则使用 flow_id 作为会话标识
    effective_session_id = session_id or flow_id
    components = []
    inputs_list = []
    types = []
    # 将输入请求列表解构为组件、输入值和类型三个独立列表
    for input_value_request in inputs:
        if input_value_request.input_value is None:
            logger.warning("InputValueRequest input_value cannot be None, defaulting to an empty string.")
            input_value_request.input_value = ""
        components.append(input_value_request.components or [])
        inputs_list.append({INPUT_FIELD_NAME: input_value_request.input_value})
        types.append(input_value_request.type)

    # 获取设置中的环境变量回退开关
    try:
        fallback_to_env_vars = get_settings_service().settings.fallback_to_env_var
    except (AttributeError, TypeError):
        fallback_to_env_vars = False

    # 设置会话 ID 并异步执行图
    graph.session_id = effective_session_id
    run_outputs = await graph.arun(
        inputs=inputs_list,
        inputs_components=components,
        types=types,
        outputs=outputs or [],
        stream=stream,
        session_id=effective_session_id or "",
        fallback_to_env_vars=fallback_to_env_vars,
        event_manager=event_manager,
    )
    return run_outputs, effective_session_id


async def run_graph(
    graph: Graph,
    input_value: str,
    input_type: str,
    output_type: str,
    *,
    session_id: str | None = None,
    fallback_to_env_vars: bool = False,
    output_component: str | None = None,
    stream: bool = False,
) -> list[RunOutputs]:
    """Runs the given Langflow Graph with the specified input and returns the outputs.
    使用指定输入运行给定的 Langflow 图并返回输出结果。

    Args:
        graph (Graph): The graph to be executed.
        input_value (str): The input value to be passed to the graph.
        input_type (str): The type of the input value.
        output_type (str): The type of the desired output.
        session_id (str | None, optional): The session ID to be used for the flow. Defaults to None.
        fallback_to_env_vars (bool, optional): Whether to fallback to environment variables.
            Defaults to False.
        output_component (Optional[str], optional): The specific output component to retrieve. Defaults to None.
        stream (bool, optional): Whether to stream the results or not. Defaults to False.

    Returns:
        List[RunOutputs]: A list of RunOutputs objects representing the outputs of the graph.

    """
    # 将输入封装为 InputValue 对象列表
    inputs = [InputValue(components=[], input_value=input_value, type=input_type)]
    # 确定输出节点：指定组件 > debug 模式（所有输出） > 按类型匹配
    if output_component:
        outputs = [output_component]
    else:
        outputs = [
            vertex.id
            for vertex in graph.vertices
            if output_type == "debug"
            or (vertex.is_output and (output_type == "any" or output_type in vertex.id.lower()))
        ]
    components = []
    inputs_list = []
    types = []
    # 将输入请求解构为组件列表、输入字典和类型列表
    for input_value_request in inputs:
        if input_value_request.input_value is None:
            logger.warning("InputValueRequest input_value cannot be None, defaulting to an empty string.")
            input_value_request.input_value = ""
        components.append(input_value_request.components or [])
        inputs_list.append({INPUT_FIELD_NAME: input_value_request.input_value})
        types.append(input_value_request.type)
    return await graph.arun(
        inputs_list,
        inputs_components=components,
        types=types,
        outputs=outputs or [],
        stream=stream,
        session_id=session_id,
        fallback_to_env_vars=fallback_to_env_vars,
    )


def validate_input(
    graph_data: dict[str, Any], tweaks: Tweaks | dict[str, str | dict[str, Any]]
) -> list[dict[str, Any]]:
    """验证图数据和调整参数的基本类型和结构，返回节点列表。"""
    if not isinstance(graph_data, dict) or not isinstance(tweaks, dict):
        msg = "graph_data and tweaks should be dictionaries"
        raise TypeError(msg)

    # 支持两种节点存放位置：data.nodes 或直接 nodes
    nodes = graph_data.get("data", {}).get("nodes") or graph_data.get("nodes")

    if not isinstance(nodes, list):
        msg = "graph_data should contain a list of nodes under 'data' key or directly under 'nodes' key"
        raise TypeError(msg)

    return nodes


def apply_tweaks(node: dict[str, Any], node_tweaks: dict[str, Any]) -> None:
    """将调整参数应用到节点的模板数据中，根据字段类型采用不同的写入策略。"""
    # 获取节点模板数据：node -> template
    template_data = node.get("data", {}).get("node", {}).get("template")

    if not isinstance(template_data, dict):
        logger.warning(f"Template data for node {node.get('id')} should be a dictionary")
        return

    for tweak_name, tweak_value in node_tweaks.items():
        # 跳过不在模板中的字段
        if tweak_name not in template_data:
            continue
        # 安全限制：code 字段不允许通过 tweaks 覆盖
        if tweak_name == "code":
            logger.warning("Security: Code field cannot be overridden via tweaks.")
            continue
        if tweak_name in template_data:
            field_type = template_data[tweak_name].get("type", "")
            if field_type == "NestedDict":
                # 嵌套字典类型：先验证/修复 JSON，再赋值
                value = validate_and_repair_json(tweak_value)
                template_data[tweak_name]["value"] = value
            elif field_type == "mcp":
                # MCP fields expect dict values to be set directly
                # MCP 字段直接设置字典值
                template_data[tweak_name]["value"] = tweak_value
            elif field_type == "dict" and isinstance(tweak_value, dict):
                # Dict fields: set the dict directly as the value.
                # If the tweak is wrapped in {"value": <actual>}, unwrap it
                # to support the template-format style (e.g. from UI exports).
                # Caveat: a legitimate single-key dict {"value": x} will be unwrapped.
                # dict 类型字段：如果被 {"value": <实际值>} 包裹则解包，否则直接赋值
                if len(tweak_value) == 1 and "value" in tweak_value:
                    template_data[tweak_name]["value"] = tweak_value["value"]
                else:
                    template_data[tweak_name]["value"] = tweak_value
            elif isinstance(tweak_value, dict):
                # 字典类型的调整值：逐个字段写入，file 类型使用 file_path 键
                for k, v in tweak_value.items():
                    k_ = "file_path" if field_type == "file" else k
                    template_data[tweak_name][k_] = v
                # If the user didn't explicitly set load_from_db in the dict,
                # we default to False for the override.
                # 如果用户未显式设置 load_from_db，默认设为 False
                if "load_from_db" not in tweak_value and "load_from_db" in template_data[tweak_name]:
                    template_data[tweak_name]["load_from_db"] = False
            else:
                # 标量类型：file 类型写入 file_path，其余写入 value
                key = "file_path" if field_type == "file" else "value"
                template_data[tweak_name][key] = tweak_value
                if "load_from_db" in template_data[tweak_name]:
                    template_data[tweak_name]["load_from_db"] = False


def apply_tweaks_on_vertex(vertex: Vertex, node_tweaks: dict[str, Any]) -> None:
    """将调整参数应用到已构建的图顶点（Vertex）上，并同步 load_from_db 字段列表。"""
    for tweak_name, tweak_value in node_tweaks.items():
        if tweak_name and tweak_value and tweak_name in vertex.params:
            vertex.params[tweak_name] = tweak_value

            # Determine if we should load from DB
            # 判断是否需要从数据库加载该字段
            tweak_load_from_db = False
            if isinstance(tweak_value, dict):
                tweak_load_from_db = tweak_value.get("load_from_db", False)

            # 同步 load_from_db_fields 列表
            if tweak_load_from_db:
                if tweak_name not in vertex.load_from_db_fields:
                    vertex.load_from_db_fields.append(tweak_name)
            elif tweak_name in vertex.load_from_db_fields:
                vertex.load_from_db_fields.remove(tweak_name)


def process_tweaks(
    graph_data: dict[str, Any], tweaks: Tweaks | dict[str, dict[str, Any]], *, stream: bool = False
) -> dict[str, Any]:
    """This function is used to tweak the graph data using the node id and the tweaks dict.
    使用节点 ID 和调整字典对图数据进行修改。

    :param graph_data: The dictionary containing the graph data. It must contain a 'data' key with
                       'nodes' as its child or directly contain 'nodes' key. Each node should have an 'id' and 'data'.
    :param tweaks: The dictionary containing the tweaks. The keys can be the node id or the name of the tweak.
                   The values can be a dictionary containing the tweaks for the node or the value of the tweak.
    :param stream: A boolean flag indicating whether streaming should be deactivated across all components or not.
                   Default is False.
    :return: The modified graph_data dictionary.
    :raises ValueError: If the input is not in the expected format.
    """
    # 将 Pydantic 模型转为字典（如果还不是的话）
    tweaks_dict = cast("dict[str, Any]", tweaks.model_dump()) if not isinstance(tweaks, dict) else tweaks
    # 如果 tweaks 中未指定 stream，将流式标志注入
    if "stream" not in tweaks_dict:
        tweaks_dict |= {"stream": stream}
    # 验证输入并提取节点列表
    nodes = validate_input(graph_data, cast("dict[str, str | dict[str, Any]]", tweaks_dict))
    # 构建节点 ID 和显示名称到节点对象的映射
    nodes_map = {node.get("id"): node for node in nodes}
    nodes_display_name_map = {node.get("data", {}).get("node", {}).get("display_name"): node for node in nodes}

    # 将 tweaks 按作用范围分类：针对特定节点的 vs 应用于所有节点的
    all_nodes_tweaks = {}
    for key, value in tweaks_dict.items():
        if isinstance(value, dict):
            # 通过节点 ID 或显示名称匹配节点，应用针对该节点的调整
            if (node := nodes_map.get(key)) or (node := nodes_display_name_map.get(key)):
                apply_tweaks(node, value)
        else:
            # 标量值作为全局调整，应用于所有节点
            all_nodes_tweaks[key] = value
    # 将全局调整应用到所有节点
    if all_nodes_tweaks:
        for node in nodes:
            apply_tweaks(node, all_nodes_tweaks)

    return graph_data


def process_tweaks_on_graph(graph: Graph, tweaks: dict[str, dict[str, Any]]):
    """将调整参数应用到图中所有匹配的顶点（Vertex）上。"""
    for vertex in graph.vertices:
        if isinstance(vertex, Vertex) and isinstance(vertex.id, str):
            node_id = vertex.id
            # 如果该顶点有对应的调整参数，则应用到顶点上
            if node_tweaks := tweaks.get(node_id):
                apply_tweaks_on_vertex(vertex, node_tweaks)
        else:
            logger.warning("Each node should be a Vertex with an 'id' attribute of type str")

    return graph
