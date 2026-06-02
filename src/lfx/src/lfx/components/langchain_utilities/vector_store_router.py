from langchain_classic.agents import AgentExecutor, create_vectorstore_router_agent
from langchain_classic.agents.agent_toolkits.vectorstore.toolkit import VectorStoreRouterToolkit

from lfx.base.agents.agent import LCAgentComponent
from lfx.inputs.inputs import HandleInput


# 向量存储路由器 Agent 组件，从向量存储路由器构建 Agent
# Vector store router agent component for building an agent from a vector store router
class VectorStoreRouterAgentComponent(LCAgentComponent):
    display_name = "VectorStoreRouterAgent"
    description = "Construct an agent from a Vector Store Router."
    name = "VectorStoreRouterAgent"
    legacy: bool = True

    inputs = [
        *LCAgentComponent.get_base_inputs(),
        HandleInput(
            name="llm",
            display_name="Language Model",
            input_types=["LanguageModel"],
            required=True,
        ),
        HandleInput(
            name="vectorstores",
            display_name="Vector Stores",
            input_types=["VectorStoreInfo"],
            is_list=True,
            required=True,
        ),
    ]

    # 构建向量存储路由器 Agent 执行器
    def build_agent(self) -> AgentExecutor:
        toolkit = VectorStoreRouterToolkit(vectorstores=self.vectorstores, llm=self.llm)
        return create_vectorstore_router_agent(llm=self.llm, toolkit=toolkit, **self.get_agent_kwargs())
