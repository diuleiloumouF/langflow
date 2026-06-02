# 自定义组件基类、数据模型
from lfx.custom.custom_component.custom_component import CustomComponent
from lfx.schema.data import Data


# 列出所有可用流程的组件（已弃用）
class ListFlowsComponent(CustomComponent):
    display_name = "List Flows"
    # 组件描述：列出所有可用的流程
    description = "A component to list all available flows."
    icon = "ListFlows"
    beta: bool = True
    name = "ListFlows"

    # 构建配置
    def build_config(self):
        return {}

    async def build(
        self,
    ) -> list[Data]:
        flows = await self.alist_flows()
        self.status = flows
        return flows
