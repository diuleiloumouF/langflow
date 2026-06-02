# 子流程组件模块
# 提供将一个完整流程封装为子流程的功能，允许在其他流程中复用已有流程的逻辑

from typing import Any

from lfx.base.flow_processing.utils import build_data_from_result_data
from lfx.custom.custom_component.component import Component
from lfx.graph.graph.base import Graph
from lfx.graph.vertex.base import Vertex
from lfx.helpers import get_flow_inputs
from lfx.io import DropdownInput, Output
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.dotdict import dotdict


# 子流程组件：将流程封装为可复用的子流程组件，提供该流程的所有输入参数作为组件输入
# 该组件已标记为遗留组件（legacy），推荐使用 logic.RunFlow 替代
class SubFlowComponent(Component):
    # 组件在画布上显示的名称
    display_name = "Sub Flow"
    # 组件描述
    description = "Generates a Component from a Flow, with all of its inputs, and "
    # 组件内部标识名
    name = "SubFlow"
    # 标记为遗留组件，不再维护
    legacy: bool = True
    # 推荐的替代组件
    replacement = ["logic.RunFlow"]
    # 组件图标
    icon = "Workflow"

    # 获取所有可用流程的名称列表，用于下拉菜单选项
    async def get_flow_names(self) -> list[str]:
        flow_data = await self.alist_flows()
        return [flow_data.data["name"] for flow_data in flow_data]

    # 根据流程名称获取对应的流程数据，未找到返回 None
    async def get_flow(self, flow_name: str) -> Data | None:
        flow_datas = await self.alist_flows()
        for flow_data in flow_datas:
            if flow_data.data["name"] == flow_name:
                return flow_data
        return None

    # 动态更新组件的构建配置
    # 当用户选择不同的流程时，动态加载该流程的输入参数作为组件的输入
    async def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        if field_name == "flow_name":
            build_config["flow_name"]["options"] = await self.get_flow_names()

        for key in list(build_config.keys()):
            if key not in [x.name for x in self.inputs] + ["code", "_type", "get_final_results_only"]:
                del build_config[key]
        if field_value is not None and field_name == "flow_name":
            try:
                flow_data = await self.get_flow(field_value)
            except Exception:  # noqa: BLE001
                await logger.aexception(f"Error getting flow {field_value}")
            else:
                if not flow_data:
                    msg = f"Flow {field_value} not found."
                    await logger.aerror(msg)
                else:
                    try:
                        graph = Graph.from_payload(flow_data.data["data"])
                        # Get all inputs from the graph
                        inputs = get_flow_inputs(graph)
                        # Add inputs to the build config
                        build_config = self.add_inputs_to_build_config(inputs, build_config)
                    except Exception:  # noqa: BLE001
                        await logger.aexception(f"Error building graph for flow {field_value}")

        return build_config

    # 将流程中所有输入节点的参数添加到构建配置中
    # 参数名格式为 "节点ID|参数名"，显示名格式为 "节点显示名 - 参数显示名"
    def add_inputs_to_build_config(self, inputs_vertex: list[Vertex], build_config: dotdict):
        new_fields: list[dotdict] = []

        for vertex in inputs_vertex:
            new_vertex_inputs = []
            field_template = vertex.data["node"]["template"]
            for inp in field_template:
                if inp not in {"code", "_type"}:
                    field_template[inp]["display_name"] = (
                        vertex.display_name + " - " + field_template[inp]["display_name"]
                    )
                    field_template[inp]["name"] = vertex.id + "|" + inp
                    new_vertex_inputs.append(field_template[inp])
            new_fields += new_vertex_inputs
        for field in new_fields:
            build_config[field["name"]] = field
        return build_config

    # 组件输入定义
    inputs = [
        # 流程选择下拉框，支持实时刷新流程列表
        DropdownInput(
            name="flow_name",
            display_name="Flow Name",
            info="The name of the flow to run.",
            options=[],
            refresh_button=True,
            real_time_refresh=True,
        ),
    ]

    # 组件输出定义：流程执行结果
    outputs = [Output(name="flow_outputs", display_name="Flow Outputs", method="generate_results")]

    # 执行子流程并返回结果数据
    # 从组件属性中提取各节点的参数，构建 tweaks 字典传给流程执行引擎
    async def generate_results(self) -> list[Data]:
        # 构建流程执行的参数调整字典
        tweaks: dict = {}
        for field in self._attributes:
            # 属性名格式为 "节点ID|参数名"，用于将参数映射到对应节点
            if field != "flow_name" and "|" in field:
                [node, name] = field.split("|")
                if node not in tweaks:
                    tweaks[node] = {}
                tweaks[node][name] = self._attributes[field]
        flow_name = self._attributes.get("flow_name")
        # 执行流程
        run_outputs = await self.run_flow(
            tweaks=tweaks,
            flow_name=flow_name,
            output_type="all",
        )
        # 收集流程执行结果
        data: list[Data] = []
        if not run_outputs:
            return data
        run_output = run_outputs[0]

        # 将流程输出结果转换为 Data 对象列表
        if run_output is not None:
            for output in run_output.outputs:
                if output:
                    data.extend(build_data_from_result_data(output))
        return data
