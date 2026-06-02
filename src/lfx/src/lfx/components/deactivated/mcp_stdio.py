# from lfx.field_typing import Data

# LangChain 结构化工具
from langchain_core.tools import StructuredTool

# MCP 协议类型
from mcp import types

# MCP 工具函数
from lfx.base.mcp.util import (
    MCPStdioClient,
    create_input_schema_from_json_schema,
    create_tool_coroutine,
    create_tool_func,
)

# 组件基类
from lfx.custom.custom_component.component import Component

# 工具类型
from lfx.field_typing import Tool

# 输入输出组件类型
from lfx.io import MessageTextInput, Output


# MCP Stdio 工具组件（已弃用），通过标准输入/输出连接 MCP 服务器并暴露其工具
class MCPStdio(Component):
    # MCP Stdio 客户端实例
    client = MCPStdioClient()
    # 工具列表结果
    tools = types.ListToolsResult
    # 工具名称列表
    tool_names = [str]
    display_name = "MCP Tools (stdio) [DEPRECATED]"
    description = (
        "Connects to an MCP server over stdio and exposes it's tools as langflow tools to be used by an Agent."
    )
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "code"
    name = "MCPStdio"
    legacy = True

    # 输入参数定义
    inputs = [
        # MCP 命令
        MessageTextInput(
            name="command",
            display_name="mcp command",
            info="mcp command",
            value="uvx mcp-sse-shim@latest",
            tool_mode=True,
        ),
    ]

    # 输出参数定义
    outputs = [
        Output(display_name="Tools", name="tools", method="build_output"),
    ]

    # 异步构建输出：连接 MCP 服务器并获取工具列表
    async def build_output(self) -> list[Tool]:
        # 如果尚未连接，则连接到 MCP 服务器
        if self.client.session is None:
            self.tools = await self.client.connect_to_server(self.command)

        tool_list = []

        # 将 MCP 工具转换为 LangChain 结构化工具
        for tool in self.tools:
            args_schema = create_input_schema_from_json_schema(tool.inputSchema)
            tool_list.append(
                StructuredTool(
                    name=tool.name,
                    description=tool.description,
                    args_schema=args_schema,
                    func=create_tool_func(tool.name, args_schema, self.client.session),
                    coroutine=create_tool_coroutine(tool.name, args_schema, self.client.session),
                )
            )
        # 记录工具名称列表
        self.tool_names = [tool.name for tool in self.tools]
        return tool_list
