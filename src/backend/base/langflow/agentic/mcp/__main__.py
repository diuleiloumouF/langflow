"""Entry point for running the Langflow Agentic MCP server.

This allows running the server with:
    python -m langflow.agentic.mcp
"""

# 运行 Langflow Agentic MCP 服务器的入口点。
# 允许通过以下命令启动服务器：python -m langflow.agentic.mcp

from langflow.agentic.mcp.server import mcp  # 从 MCP 服务器模块导入 mcp 实例

if __name__ == "__main__":
    mcp.run()  # 启动 MCP 服务器
