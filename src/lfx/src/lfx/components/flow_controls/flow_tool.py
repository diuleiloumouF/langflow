from typing import Any

from typing_extensions import override

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.base.tools.flow_tool import FlowTool
from lfx.field_typing import Tool
from lfx.graph.graph.base import Graph
from lfx.helpers import get_flow_inputs
from lfx.io import BoolInput, DropdownInput, Output, StrInput
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.dotdict import dotdict


class FlowToolComponent(LCToolComponent):
    """将已加载的 Flow 封装为一个可调用的 Tool 组件。

    用户可以从下拉列表中选择一个 Flow，将其转换为 LangChain Tool，
    以便在其他 Flow 中作为工具调用。该组件已标记为 legacy，
    推荐使用 logic.RunFlow 替代。
    """

    # 组件在画布上的显示名称
    display_name = "Flow as Tool"
    # 组件的描述信息
    description = "Construct a Tool from a function that runs the loaded Flow."
    # 属性在配置面板中的显示顺序
    field_order = ["flow_name", "name", "description", "return_direct"]
    # 追踪类型，用于可观测性
    trace_type = "tool"
    # 工具名称
    name = "FlowTool"
    # 标记为遗留组件，不再推荐使用
    legacy: bool = True
    # 推荐的替代组件
    replacement = ["logic.RunFlow"]
    # 画布上显示的图标
    icon = "hammer"

    async def get_flow_names(self) -> list[str]:
        """获取当前用户所有可用 Flow 的名称列表。"""
        flow_datas = await self.alist_flows()
        return [flow_data.data["name"] for flow_data in flow_datas]

    async def get_flow(self, flow_name: str) -> Data | None:
        """Retrieves a flow by its name.

        通过名称查找并返回对应的 Flow 记录。

        Args:
            flow_name (str): The name of the flow to retrieve.

        Returns:
            Optional[Text]: The flow record if found, None otherwise.
        """
        flow_datas = await self.alist_flows()
        for flow_data in flow_datas:
            if flow_data.data["name"] == flow_name:
                return flow_data
        return None

    @override
    async def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        """动态更新构建配置，当用户点击刷新按钮时重新加载 Flow 名称列表。"""
        if field_name == "flow_name":
            build_config["flow_name"]["options"] = self.get_flow_names()

        return build_config

    # 组件输入参数定义
    inputs = [
        # 下拉选择要运行的 Flow
        DropdownInput(
            name="flow_name", display_name="Flow Name", info="The name of the flow to run.", refresh_button=True
        ),
        # 工具名称，用于在其他 Flow 中引用
        StrInput(
            name="tool_name",
            display_name="Name",
            info="The name of the tool.",
        ),
        # 工具描述，默认使用 Flow 自身的描述
        StrInput(
            name="tool_description",
            display_name="Description",
            info="The description of the tool; defaults to the Flow's description.",
        ),
        # 是否直接返回结果（高级选项）
        BoolInput(
            name="return_direct",
            display_name="Return Direct",
            info="Return the result directly from the Tool.",
            advanced=True,
        ),
    ]

    # 组件输出定义：构建一个 Tool 对象
    outputs = [
        Output(name="api_build_tool", display_name="Tool", method="build_tool"),
    ]

    async def build_tool(self) -> Tool:
        """构建并返回一个封装了目标 Flow 的 FlowTool 实例。

        执行流程：
        1. 根据用户选择的 flow_name 查找对应的 Flow 记录
        2. 将 Flow 的 JSON 数据解析为 Graph 对象
        3. 从 Graph 中提取输入参数信息
        4. 创建 FlowTool 实例并设置其名称、描述等属性
        5. 将工具的参数信息格式化到组件状态中，便于用户查看
        """
        FlowTool.model_rebuild()
        # 校验 flow_name 参数是否已提供
        if "flow_name" not in self._attributes or not self._attributes["flow_name"]:
            msg = "Flow name is required"
            raise ValueError(msg)
        flow_name = self._attributes["flow_name"]
        # 根据名称查找 Flow 记录
        flow_data = await self.get_flow(flow_name)
        if not flow_data:
            msg = "Flow not found."
            raise ValueError(msg)
        # 将 Flow 数据解析为可执行的 Graph 对象
        graph = Graph.from_payload(
            flow_data.data["data"],
            user_id=str(self.user_id),
        )
        # 尝试将当前运行的 run_id 传递给子图，用于链路追踪
        try:
            graph.set_run_id(self.graph.run_id)
        except Exception:  # noqa: BLE001
            logger.warning("Failed to set run_id", exc_info=True)
        # 提取 Flow 的输入参数定义
        inputs = get_flow_inputs(graph)
        # 工具描述：优先使用用户自定义描述，否则使用 Flow 的描述
        tool_description = self.tool_description.strip() or flow_data.description
        # 创建 FlowTool 实例
        tool = FlowTool(
            name=self.tool_name,
            description=tool_description,
            graph=graph,
            return_direct=self.return_direct,
            inputs=inputs,
            flow_id=str(flow_data.id),
            user_id=str(self.user_id),
            session_id=self.graph.session_id if hasattr(self, "graph") else None,
        )
        # 将工具描述和参数信息格式化为状态字符串，显示在组件状态面板中
        description_repr = repr(tool.description).strip("'")
        args_str = "\n".join([f"- {arg_name}: {arg_data['description']}" for arg_name, arg_data in tool.args.items()])
        self.status = f"{description_repr}\nArguments:\n{args_str}"
        return tool
