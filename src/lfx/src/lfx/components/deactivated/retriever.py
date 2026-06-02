# LangChain 检索器工具创建函数
from langchain_core.tools import create_retriever_tool

# 自定义组件基类
from lfx.custom.custom_component.custom_component import CustomComponent

# 类型定义
from lfx.field_typing import BaseRetriever, Tool

# 输入组件类型
from lfx.io import HandleInput, StrInput


# 检索器工具组件，将检索器包装为可被 Agent 使用的工具
class RetrieverToolComponent(CustomComponent):
    display_name = "RetrieverTool"
    description = "Tool for interacting with retriever"
    name = "RetrieverTool"
    icon = "LangChain"
    legacy = True

    # 输入参数定义
    inputs = [
        # 检索器实例
        HandleInput(
            name="retriever",
            display_name="Retriever",
            info="Retriever to interact with",
            input_types=["Retriever"],
            required=True,
        ),
        StrInput(
            name="name",
            display_name="Name",
            info="Name of the tool",
            required=True,
        ),
        StrInput(
            name="description",
            display_name="Description",
            info="Description of the tool",
            required=True,
        ),
    ]

    def build(self, retriever: BaseRetriever, name: str, description: str, **kwargs) -> Tool:
        _ = kwargs
        return create_retriever_tool(
            retriever=retriever,
            name=name,
            description=description,
        )
