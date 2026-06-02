from datetime import datetime
from typing import Any

from lfx.base.tools.run_flow import RunFlowBaseComponent
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.dotdict import dotdict


class RunFlowComponent(RunFlowBaseComponent):
    """运行流程组件。

    用于在同一项目内执行另一个流程，也可以作为代理工具使用。
    继承自 RunFlowBaseComponent，提供了流程选择、加载和更新的完整功能。
    """

    # 显示名称，用于在 Langflow 界面中展示
    display_name = "Run Flow"
    # 组件描述信息，包含工具模式的说明
    description = (
        "Executes another flow from within the same project. Can also be used as a tool for agents."
        " \n **Select a Flow to use the tool mode**"
    )
    # 组件文档链接
    documentation: str = "https://docs.langflow.org/run-flow"
    # 标记为 Beta 功能
    beta = True
    # 组件内部名称，用于系统标识
    name = "RunFlow"
    # 组件图标
    icon = "Workflow"

    # 从基类获取输入参数定义
    inputs = RunFlowBaseComponent.get_base_inputs()
    # 从基类获取输出参数定义
    outputs = RunFlowBaseComponent.get_base_outputs()

    async def update_build_config(
        self,
        build_config: dotdict,
        field_value: Any,
        field_name: str | None = None,
    ):
        """更新构建配置。

        当用户在界面上选择流程或点击刷新时，该方法会：
        1. 补充缺失的配置键（如 flow_name_selected、flow_id_selected 等）
        2. 刷新时重新加载所有可用流程列表
        3. 选中流程时加载对应的图结构并更新配置
        """
        # 检查 build_config 中是否缺少必要的键，并为其设置默认值
        missing_keys = [key for key in self.default_keys if key not in build_config]
        for key in missing_keys:  # TODO: create a defaults dict to avoid hardcoding the defaults here
            if key == "flow_name_selected":
                # 流程名称选择字段，默认为空选项列表
                build_config[key] = {"options": [], "options_metadata": [], "value": None}
            elif key == "flow_id_selected":
                # 流程 ID 选择字段，默认无值
                build_config[key] = {"value": None}
            elif key == "cache_flow":
                # 流程缓存开关，默认关闭
                build_config[key] = {"value": False}
            else:
                build_config[key] = {}
        # 处理流程名称选择或组件初始化/刷新的情况
        if field_name == "flow_name_selected" and (build_config.get("is_refresh", False) or field_value is None):
            # refresh button was clicked or componented was initialized, so list the flows
            # 用户点击了刷新按钮或组件初始化，重新列出所有可用流程
            options: list[str] = await self.alist_flows_by_flow_folder()
            # 将流程名称列表填入选项
            build_config["flow_name_selected"]["options"] = [flow.data["name"] for flow in options]
            build_config["flow_name_selected"]["options_metadata"] = []
            for flow in options:
                # populate options_metadata
                # 填充选项元数据（包含流程 ID 和更新时间）
                build_config["flow_name_selected"]["options_metadata"].append(
                    {"id": flow.data["id"], "updated_at": flow.data["updated_at"]}
                )
                # update selected flow if it is stale
                # 如果当前选中的流程有更新，则自动刷新
                if str(flow.data["id"]) == self.flow_id_selected:
                    await self.check_and_update_stale_flow(flow, build_config)
        elif field_name in {"flow_name_selected", "flow_id_selected"} and field_value is not None:
            # flow was selected by name or id, so get the flow and update the bcfg
            # 用户通过名称或 ID 选择了流程，加载流程图并更新构建配置
            try:
                # derive flow id if the field_name is flow_name_selected
                # 如果是通过名称选择，则从元数据中获取对应的流程 ID
                build_config["flow_id_selected"]["value"] = (
                    self.get_selected_flow_meta(build_config, "id") or build_config["flow_id_selected"]["value"]
                )
                updated_at = self.get_selected_flow_meta(build_config, "updated_at")
                # 加载流程图并更新构建配置
                await self.load_graph_and_update_cfg(
                    build_config, build_config["flow_id_selected"]["value"], updated_at
                )
            except Exception as e:
                msg = f"Error building graph for flow {field_value}"
                await logger.aexception(msg)
                raise RuntimeError(msg) from e

        return build_config

    def get_selected_flow_meta(self, build_config: dotdict, field: str) -> dict:
        """Get the selected flow's metadata from the build config."""
        # 从构建配置中获取当前选中流程的指定元数据字段
        return build_config.get("flow_name_selected", {}).get("selected_metadata", {}).get(field)

    async def load_graph_and_update_cfg(
        self,
        build_config: dotdict,
        flow_id: str,
        updated_at: str | datetime,
    ) -> None:
        """Load a flow's graph and update the build config."""
        # 根据流程 ID 加载流程图，并将图结构信息写入构建配置
        graph = await self.get_graph(
            flow_id_selected=flow_id,
            updated_at=self.get_str_isots(updated_at),
        )
        self.update_build_config_from_graph(build_config, graph)

    def should_update_stale_flow(self, flow: Data, build_config: dotdict) -> bool:
        """Check if the flow should be updated."""
        # 判断流程是否已过时：数据库中的更新时间晚于构建配置中记录的更新时间时视为过时
        return (
            (updated_at := self.get_str_isots(flow.data["updated_at"]))  # true updated_at date just fetched from db
            and (stale_at := self.get_selected_flow_meta(build_config, "updated_at"))  # outdated date in bcfg
            and self._parse_timestamp(updated_at) > self._parse_timestamp(stale_at)  # stale flow condition
        )

    async def check_and_update_stale_flow(self, flow: Data, build_config: dotdict) -> None:
        """Check if the flow should be updated and update it if necessary."""
        # TODO: improve contract/return value
        # 如果检测到流程已过时，则重新加载流程图并更新构建配置
        if self.should_update_stale_flow(flow, build_config):
            await self.load_graph_and_update_cfg(
                build_config,
                flow.data["id"],
                flow.data["updated_at"],
            )

    def get_str_isots(self, date: datetime | str) -> str:
        """Get a string timestamp from a datetime or string."""
        # 将 datetime 对象转换为 ISO 格式字符串，如果已经是字符串则直接返回
        return date.isoformat() if hasattr(date, "isoformat") else date
