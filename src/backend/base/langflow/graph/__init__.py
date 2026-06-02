# 从 lfx 包导入图（Graph）相关的核心类
from lfx.graph.edge.base import Edge  # 边：表示流程中组件之间的连接关系
from lfx.graph.graph.base import Graph  # 图：表示整个工作流的结构和执行逻辑
from lfx.graph.vertex.base import Vertex  # 顶点：表示流程中的一个节点/组件
from lfx.graph.vertex.vertex_types import CustomComponentVertex, InterfaceVertex, StateVertex

# CustomComponentVertex: 自定义组件顶点，用于动态加载的用户自定义组件
# InterfaceVertex: 接口顶点，用于与外部系统交互的节点
# StateVertex: 状态顶点，用于维护和传递状态信息的节点

# 模块的公开接口，定义了从该包导出的所有类
__all__ = ["CustomComponentVertex", "Edge", "Graph", "InterfaceVertex", "StateVertex", "Vertex"]
