"""MCP (Model Context Protocol) server for Langflow Agentic tools."""
# MCP（模型上下文协议）服务器，用于 Langflow 的智能工具模块

from langflow.agentic.mcp.server import mcp

# 从 mcp.server 模块导入 mcp 服务器实例

__all__ = ["mcp"]
# 定义模块公开接口，仅导出 mcp 服务器实例
