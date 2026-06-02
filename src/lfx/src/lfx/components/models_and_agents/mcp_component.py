"""MCP Tools 组件 — 连接 MCP 服务器并调用其工具。

该模块提供 MCPToolsComponent 组件，用于：
- 连接到 MCP (Model Context Protocol) 服务器
- 获取服务器上可用的工具列表
- 执行用户选择的工具并返回结果
- 支持缓存机制以提升性能
- 支持 stdio 和 Streamable HTTP 两种 MCP 传输协议
"""

from __future__ import annotations

import asyncio
import json
import uuid
from types import UnionType
from typing import Any, get_args, get_origin

from langchain_core.tools import StructuredTool  # noqa: TC002
from pydantic import BaseModel

from lfx.base.agents.utils import maybe_unflatten_dict, safe_cache_get, safe_cache_set
from lfx.base.mcp.util import (
    MCPStdioClient,  # MCP stdio 传输客户端
    MCPStreamableHttpClient,  # MCP Streamable HTTP 传输客户端
    update_tools,  # 更新工具列表的工具函数
)
from lfx.custom.custom_component.component_with_cache import ComponentWithCache
from lfx.inputs.inputs import InputTypes  # noqa: TC001
from lfx.io import BoolInput, DictInput, DropdownInput, McpInput, MessageTextInput, Output
from lfx.io.schema import schema_to_langflow_inputs
from lfx.log.logger import logger
from lfx.schema.dataframe import DataFrame
from lfx.schema.message import Message
from lfx.services.deps import get_storage_service, session_scope


def resolve_mcp_config(
    server_name: str,  # noqa: ARG001
    server_config_from_value: dict | None,
    server_config_from_db: dict | None,
) -> dict | None:
    """根据优先级解析 MCP 服务器配置。

    Resolves the configuration for an MCP server with the following precedence:
    1. Database config (takes priority) - ensures edits are reflected
    2. Config from value/tweaks (fallback) - allows REST API to provide config for new servers

    优先级规则：
    1. 数据库配置（优先）- 确保编辑操作能够生效
    2. 通过 value/tweaks 传入的配置（回退）- 允许 REST API 为新服务器提供配置

    Args:
        server_name: MCP 服务器的名称
        server_config_from_value: 通过 value/tweaks 传入的配置（可选）
        server_config_from_db: 来自数据库的配置（可选）

    Returns:
        最终使用的配置（数据库优先，回退到 value）
        如果两个位置都没有找到配置则返回 None
    """
    if server_config_from_db:
        return server_config_from_db
    return server_config_from_value


class MCPToolsComponent(ComponentWithCache):
    """MCP 工具组件 — 连接到 MCP 服务器并使用其提供的工具。

    该组件支持两种 MCP 传输协议：
    - stdio: 通过标准输入输出与本地 MCP 服务器通信
    - Streamable HTTP: 通过 HTTP 与远程 MCP 服务器通信

    主要功能：
    - 从 MCP 服务器获取可用工具列表
    - 根据工具的 schema 动态生成输入表单
    - 执行用户选择的工具并返回 DataFrame 格式的结果
    - 支持可选的缓存机制以提升性能
    - 支持自定义 HTTP 请求头（如认证头）
    """

    schema_inputs: list = []  # 当前工具的输入 schema 列表
    tools: list[StructuredTool] = []  # 从 MCP 服务器获取的工具列表
    _not_load_actions: bool = False  # 标记是否跳过工具加载（用于 tool_mode 场景）
    _tool_cache: dict = {}  # 工具缓存，键为工具名，值为工具对象
    _last_selected_server: str | None = None  # Cache for the last selected server
    # 上次选中的服务器名称缓存，用于判断服务器是否切换

    def __init__(self, **data) -> None:
        """初始化 MCP 工具组件。

        设置缓存结构，并创建两种 MCP 传输客户端（stdio 和 HTTP）。
        """
        super().__init__(**data)
        # Initialize cache keys to avoid CacheMiss when accessing them
        # 初始化缓存键结构，避免访问时出现 CacheMiss
        self._ensure_cache_structure()

        # Initialize clients with access to the component cache
        # 初始化客户端，使其可以访问组件级共享缓存
        self.stdio_client: MCPStdioClient = MCPStdioClient(component_cache=self._shared_component_cache)
        self.streamable_http_client: MCPStreamableHttpClient = MCPStreamableHttpClient(
            component_cache=self._shared_component_cache
        )

    def _ensure_cache_structure(self):
        """确保缓存具有所需的初始化结构。

        初始化 "servers"（服务器缓存）和 "last_selected_server"（上次选中的服务器）两个缓存键。
        """
        # Check if servers key exists and is not CacheMiss
        # 检查 "servers" 缓存键是否存在且不是 CacheMiss
        servers_value = safe_cache_get(self._shared_component_cache, "servers")
        if servers_value is None:
            safe_cache_set(self._shared_component_cache, "servers", {})

        # Check if last_selected_server key exists and is not CacheMiss
        # 检查 "last_selected_server" 缓存键是否存在且不是 CacheMiss
        last_server_value = safe_cache_get(self._shared_component_cache, "last_selected_server")
        if last_server_value is None:
            safe_cache_set(self._shared_component_cache, "last_selected_server", "")

    # 默认配置键列表 — 这些键不会在工具切换时被清除
    default_keys: list[str] = [
        "code",
        "_type",
        "tool_mode",
        "tool_placeholder",
        "mcp_server",
        "tool",
        "use_cache",
        "verify_ssl",
        "headers",
    ]

    display_name = "MCP Tools"
    description = "Connect to an MCP server to use its tools."
    documentation: str = "https://docs.langflow.org/mcp-tools"
    icon = "Mcp"
    name = "MCPTools"

    inputs = [
        McpInput(
            name="mcp_server",
            display_name="MCP Server",
            info="Select the MCP Server that will be used by this component",
            real_time_refresh=True,
        ),
        BoolInput(
            name="use_cache",
            display_name="Use Cached Server",
            info=(
                "Enable caching of MCP Server and tools to improve performance. "
                "Disable to always fetch fresh tools and server updates."
            ),
            value=False,
            advanced=True,
        ),
        BoolInput(
            name="verify_ssl",
            display_name="Verify SSL Certificate",
            info=(
                "Enable SSL certificate verification for HTTPS connections. "
                "Disable only for development/testing with self-signed certificates."
            ),
            value=True,
            advanced=True,
        ),
        DictInput(
            name="headers",
            display_name="Headers",
            info=(
                "HTTP headers to include with MCP server requests. "
                "Useful for authentication (e.g., Authorization header). "
                "These headers override any headers configured in the MCP server settings."
            ),
            advanced=True,
            is_list=True,
        ),
        DropdownInput(
            name="tool",
            display_name="Tool",
            options=[],
            value="",
            info="Select the tool to execute",
            show=False,
            required=True,
            real_time_refresh=True,
            refresh_button=True,
        ),
        MessageTextInput(
            name="tool_placeholder",
            display_name="Tool Placeholder",
            info="Placeholder for the tool",
            value="",
            show=False,
            tool_mode=False,
        ),
    ]

    outputs = [
        Output(display_name="Response", name="response", method="build_output"),
    ]

    async def _validate_schema_inputs(self, tool_obj) -> list[InputTypes]:
        """验证并处理工具的输入 schema。

        将工具对象的 args_schema 转换为 Langflow 输入组件列表。
        """
        # Validate and process schema inputs for a tool.
        # 验证并处理工具的 schema 输入参数
        try:
            if not tool_obj or not hasattr(tool_obj, "args_schema"):
                msg = "Invalid tool object or missing input schema"
                raise ValueError(msg)

            input_schema = tool_obj.args_schema
            if not input_schema:
                msg = f"Empty input schema for tool '{tool_obj.name}'"
                raise ValueError(msg)

            schema_inputs = schema_to_langflow_inputs(input_schema)
            if not schema_inputs:
                msg = f"No input parameters defined for tool '{tool_obj.name}'"
                await logger.awarning(msg)
                return []

        except Exception as e:
            msg = f"Error validating schema inputs: {e!s}"
            await logger.aexception(msg)
            raise ValueError(msg) from e
        else:
            return schema_inputs

    async def update_tool_list(self, mcp_server_value=None):
        """从 MCP 服务器获取并更新工具列表。

        处理流程：
        1. 检查缓存是否可用
        2. 从数据库获取最新的服务器配置
        3. 根据优先级解析最终配置（数据库优先）
        4. 合并组件级别的 HTTP 请求头
        5. 调用 MCP 客户端获取工具列表
        6. 将结果存入缓存（如果启用了缓存）

        Args:
            mcp_server_value: 服务器配置字典 {name, config}，或服务器名称字符串

        Returns:
            (工具列表, 服务器配置字典) 的元组
        """
        # Accepts mcp_server_value as dict {name, config} or uses self.mcp_server
        # 接受 dict {name, config} 格式的服务器值，或使用 self.mcp_server
        mcp_server = mcp_server_value if mcp_server_value is not None else getattr(self, "mcp_server", None)
        server_name = None
        server_config_from_value = None
        if isinstance(mcp_server, dict):
            server_name = mcp_server.get("name")
            server_config_from_value = mcp_server.get("config")
        else:
            server_name = mcp_server
        if not server_name:
            self.tools = []
            return [], {"name": server_name, "config": server_config_from_value}

        # Check if caching is enabled, default to False
        # 检查是否启用了缓存，默认为 False
        use_cache = getattr(self, "use_cache", False)

        # Use shared cache if available and caching is enabled
        # 如果启用了缓存，尝试从共享缓存中获取工具数据
        cached = None
        if use_cache:
            servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
            cached = servers_cache.get(server_name) if isinstance(servers_cache, dict) else None

        if cached is not None:
            try:
                self.tools = cached["tools"]
                self.tool_names = cached["tool_names"]
                self._tool_cache = cached["tool_cache"]
                server_config_from_value = cached["config"]
            except (TypeError, KeyError, AttributeError) as e:
                # Handle corrupted cache data by clearing it and continuing to fetch fresh tools
                msg = f"Unable to use cached data for MCP Server{server_name}: {e}"
                await logger.awarning(msg)
                # Clear the corrupted cache entry
                current_servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
                if isinstance(current_servers_cache, dict) and server_name in current_servers_cache:
                    current_servers_cache.pop(server_name)
                    safe_cache_set(self._shared_component_cache, "servers", current_servers_cache)
            else:
                return self.tools, {"name": server_name, "config": server_config_from_value}

        try:
            # Try to fetch from database first to ensure we have the latest config
            # This ensures database updates (like editing a server) take effect
            # 先从数据库获取配置，确保数据库中的编辑操作能够生效
            try:
                from langflow.api.v2.mcp import get_server
                from langflow.services.database.models.user.crud import get_user_by_id

                from lfx.services.deps import get_settings_service
            except ImportError as e:
                msg = (
                    "Langflow MCP server functionality is not available. "
                    "This feature requires the full Langflow installation."
                )
                raise ImportError(msg) from e

            server_config_from_db = None
            async with session_scope() as db:
                if not self.user_id:
                    msg = "User ID is required for fetching MCP tools."
                    raise ValueError(msg)
                current_user = await get_user_by_id(db, self.user_id)

                # Try to get server config from DB/API
                server_config_from_db = await get_server(
                    server_name,
                    current_user,
                    db,
                    storage_service=get_storage_service(),
                    settings_service=get_settings_service(),
                )

            # Resolve config with proper precedence: DB takes priority, falls back to value
            # 按优先级解析配置：数据库优先，回退到传入的值
            server_config = resolve_mcp_config(
                server_name=server_name,
                server_config_from_value=server_config_from_value,
                server_config_from_db=server_config_from_db,
            )

            if not server_config:
                self.tools = []
                return [], {"name": server_name, "config": server_config}

            # Add verify_ssl option to server config if not present
            # 如果服务器配置中没有 SSL 验证选项，从组件设置中补充
            if "verify_ssl" not in server_config:
                verify_ssl = getattr(self, "verify_ssl", True)
                server_config["verify_ssl"] = verify_ssl

            # Merge headers from component input with server config headers
            # Component headers take precedence over server config headers
            # 将组件输入的请求头与服务器配置的请求头合并
            # 组件级请求头优先于服务器配置的请求头
            component_headers = getattr(self, "headers", None) or []
            if component_headers:
                # Convert list of {"key": k, "value": v} to dict
                # 将 [{"key": k, "value": v}] 格式的列表转换为字典
                component_headers_dict = {}
                if isinstance(component_headers, list):
                    for item in component_headers:
                        if isinstance(item, dict) and "key" in item and "value" in item:
                            component_headers_dict[item["key"]] = item["value"]
                elif isinstance(component_headers, dict):
                    component_headers_dict = component_headers

                if component_headers_dict:
                    existing_headers = server_config.get("headers", {}) or {}
                    # Ensure existing_headers is a dict (convert from list if needed)
                    if isinstance(existing_headers, list):
                        existing_dict = {}
                        for item in existing_headers:
                            if isinstance(item, dict) and "key" in item and "value" in item:
                                existing_dict[item["key"]] = item["value"]
                        existing_headers = existing_dict
                    merged_headers = {**existing_headers, **component_headers_dict}
                    server_config["headers"] = merged_headers
            # Get request_variables from graph context for global variable resolution
            # 从图上下文中获取全局变量，用于请求变量解析
            request_variables = None
            if hasattr(self, "graph") and self.graph and hasattr(self.graph, "context"):
                request_variables = self.graph.context.get("request_variables")

            # Only load global variables from database if we have headers that might use them
            # This avoids unnecessary database queries when headers are empty
            # 仅在有请求头需要解析全局变量时才从数据库加载，避免不必要的查询
            has_headers = server_config.get("headers") and len(server_config.get("headers", {})) > 0
            if not request_variables and has_headers:
                try:
                    from lfx.services.deps import get_variable_service

                    variable_service = get_variable_service()
                    if variable_service:
                        async with session_scope() as db:
                            request_variables = await variable_service.get_all_decrypted_variables(
                                user_id=self.user_id, session=db
                            )
                except Exception as e:  # noqa: BLE001
                    await logger.awarning(f"Failed to load global variables for MCP component: {e}")

            _, tool_list, tool_cache = await update_tools(
                server_name=server_name,
                server_config=server_config,
                mcp_stdio_client=self.stdio_client,
                mcp_streamable_http_client=self.streamable_http_client,
                request_variables=request_variables,
            )

            self.tool_names = [tool.name for tool in tool_list if hasattr(tool, "name")]
            self._tool_cache = tool_cache
            self.tools = tool_list

            # Cache the result only if caching is enabled
            # 仅在启用缓存时将结果存入缓存
            if use_cache:
                cache_data = {
                    "tools": tool_list,
                    "tool_names": self.tool_names,
                    "tool_cache": tool_cache,
                    "config": server_config,
                }

                # Safely update the servers cache
                current_servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
                if isinstance(current_servers_cache, dict):
                    current_servers_cache[server_name] = cache_data
                    safe_cache_set(self._shared_component_cache, "servers", current_servers_cache)

        except (TimeoutError, asyncio.TimeoutError) as e:
            msg = f"Timeout updating tool list: {e!s}"
            await logger.aexception(msg)
            raise TimeoutError(msg) from e
        except Exception as e:
            msg = f"Error updating tool list: {e!s}"
            await logger.aexception(msg)
            raise ValueError(msg) from e
        else:
            return tool_list, {"name": server_name, "config": server_config}

    async def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None) -> dict:
        """根据用户选择动态更新组件的构建配置（UI 表单）。

        根据字段名称分发不同的处理逻辑：
        - "tool": 工具选择变更时，加载工具的输入参数 schema
        - "mcp_server": 服务器选择变更时，刷新可用工具列表
        - "tool_mode": 工具模式切换时，控制工具下拉框的显示/隐藏
        - "tools_metadata": 工具元数据变更时的处理

        Args:
            build_config: 当前的构建配置字典
            field_value: 当前字段的新值
            field_name: 发生变更的字段名称

        Returns:
            更新后的构建配置字典
        """
        try:
            if field_name == "tool":
                try:
                    # Always refresh tools when cache is disabled, or when tools list is empty
                    # This ensures database edits are reflected immediately when cache is disabled
                    # 缓存禁用或工具列表为空时始终刷新工具，确保数据库编辑立即生效
                    use_cache = getattr(self, "use_cache", False)
                    if len(self.tools) == 0 or not use_cache:
                        try:
                            self.tools, build_config["mcp_server"]["value"] = await self.update_tool_list()
                            build_config["tool"]["options"] = [tool.name for tool in self.tools]
                            build_config["tool"]["placeholder"] = "Select a tool"
                        except (TimeoutError, asyncio.TimeoutError) as e:
                            msg = f"Timeout updating tool list: {e!s}"
                            await logger.aexception(msg)
                            if not build_config["tools_metadata"]["show"]:
                                build_config["tool"]["show"] = True
                                build_config["tool"]["options"] = []
                                build_config["tool"]["value"] = ""
                                build_config["tool"]["placeholder"] = "Timeout on MCP server"
                            else:
                                build_config["tool"]["show"] = False
                        except ValueError:
                            if not build_config["tools_metadata"]["show"]:
                                build_config["tool"]["show"] = True
                                build_config["tool"]["options"] = []
                                build_config["tool"]["value"] = ""
                                build_config["tool"]["placeholder"] = "Error on MCP Server"
                            else:
                                build_config["tool"]["show"] = False

                    if field_value == "":
                        return build_config
                    tool_obj = None
                    for tool in self.tools:
                        if tool.name == field_value:
                            tool_obj = tool
                            break
                    if tool_obj is None:
                        msg = f"Tool {field_value} not found in available tools: {self.tools}"
                        await logger.awarning(msg)
                        return build_config
                    await self._update_tool_config(build_config, field_value)
                except Exception as e:
                    build_config["tool"]["options"] = []
                    msg = f"Failed to update tools: {e!s}"
                    raise ValueError(msg) from e
                else:
                    return build_config
            elif field_name == "mcp_server":
                # 处理 MCP 服务器选择变更
                if not field_value:
                    build_config["tool"]["show"] = False
                    build_config["tool"]["options"] = []
                    build_config["tool"]["value"] = ""
                    build_config["tool"]["placeholder"] = ""
                    build_config["tool_placeholder"]["tool_mode"] = False
                    self.remove_non_default_keys(build_config)
                    return build_config

                build_config["tool_placeholder"]["tool_mode"] = True

                current_server_name = field_value.get("name") if isinstance(field_value, dict) else field_value
                _last_selected_server = safe_cache_get(self._shared_component_cache, "last_selected_server", "")
                # Only treat as a server change if there was a previous server selection.
                # Cold cache (_last_selected_server="") on initial flow load is NOT a server change —
                # the user didn't switch anything, the backend just hasn't seen this component yet.
                # 仅在有先前选择的服务器时才视为服务器切换
                # 初始加载时冷缓存（_last_selected_server=""）不算服务器切换
                server_changed = bool(_last_selected_server and current_server_name != _last_selected_server)

                # Determine if "Tool Mode" is active by checking if the tool dropdown is hidden.
                # 通过检查工具下拉框是否隐藏来判断是否处于 "工具模式"
                is_in_tool_mode = build_config["tools_metadata"]["show"]

                # Get use_cache setting to determine if we should use cached data
                # 获取缓存设置以决定是否使用缓存数据
                use_cache = getattr(self, "use_cache", False)

                # Fast path: if server didn't change and we already have options, keep them as-is
                # BUT only if caching is enabled, we're in tool mode, or it's the initial load
                # 快速路径：如果服务器未切换且已有工具选项，直接返回
                # 但仅在启用了缓存、处于工具模式或初始加载时适用
                existing_options = build_config.get("tool", {}).get("options") or []
                if not server_changed and existing_options:
                    # In non-tool mode with cache disabled, skip the fast path to force refresh
                    # BUT on initial load (cold cache), always preserve saved options from the flow
                    if not is_in_tool_mode and not use_cache and _last_selected_server:
                        pass  # Continue to refresh logic below (user-initiated with cache disabled)
                    else:
                        if not is_in_tool_mode:
                            build_config["tool"]["show"] = True
                        safe_cache_set(self._shared_component_cache, "last_selected_server", current_server_name)
                        return build_config

                # To avoid unnecessary updates, only proceed if the server has actually changed
                # OR if caching is disabled (to force refresh in non-tool mode)
                # 为避免不必要的更新，仅在服务器实际切换或缓存禁用时继续处理
                if (_last_selected_server in (current_server_name, "")) and build_config["tool"]["show"] and use_cache:
                    if current_server_name:
                        servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
                        if isinstance(servers_cache, dict):
                            cached = servers_cache.get(current_server_name)
                            if cached is not None and cached.get("tool_names"):
                                cached_tools = cached["tool_names"]
                                current_tools = build_config["tool"]["options"]
                                if current_tools == cached_tools:
                                    return build_config
                    else:
                        return build_config
                safe_cache_set(self._shared_component_cache, "last_selected_server", current_server_name)

                # When cache is disabled, clear any cached data for this server
                # This ensures we always fetch fresh data from the database
                # 缓存禁用时清除该服务器的缓存数据，确保始终从数据库获取最新数据
                if not use_cache and current_server_name:
                    servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
                    if isinstance(servers_cache, dict) and current_server_name in servers_cache:
                        servers_cache.pop(current_server_name)
                        safe_cache_set(self._shared_component_cache, "servers", servers_cache)

                # Check if tools are already cached for this server before clearing
                # 在清除之前检查该服务器的工具是否已缓存
                cached_tools = None
                if current_server_name and use_cache:
                    servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
                    if isinstance(servers_cache, dict):
                        cached = servers_cache.get(current_server_name)
                        if cached is not None:
                            try:
                                cached_tools = cached["tools"]
                                self.tools = cached_tools
                                self.tool_names = cached["tool_names"]
                                self._tool_cache = cached["tool_cache"]
                            except (TypeError, KeyError, AttributeError) as e:
                                # Handle corrupted cache data by ignoring it
                                msg = f"Unable to use cached data for MCP Server,{current_server_name}: {e}"
                                await logger.awarning(msg)
                                cached_tools = None

                # Clear tools when cache is disabled OR when we don't have cached tools
                # This ensures fresh tools are fetched after database edits
                # 缓存禁用或没有缓存工具时清空工具列表，确保获取最新工具
                if not cached_tools or not use_cache:
                    self.tools = []  # Clear previous tools to force refresh

                # Clear previous tool inputs if:
                # 1. Server actually changed
                # 2. Cache is disabled (meaning tool list will be refreshed)
                # 清除之前的工具输入：1. 服务器切换了  2. 缓存禁用（工具列表将刷新）
                if server_changed or not use_cache:
                    self.remove_non_default_keys(build_config)

                # Only show the tool dropdown if not in tool_mode
                # 仅在非工具模式下显示工具下拉框
                if not is_in_tool_mode:
                    build_config["tool"]["show"] = True
                    if cached_tools:
                        # Use cached tools to populate options immediately
                        build_config["tool"]["options"] = [tool.name for tool in cached_tools]
                        build_config["tool"]["placeholder"] = "Select a tool"
                    else:
                        # Actually fetch tools now instead of deferring to a frontend callback.
                        # The frontend has no reliable mechanism to trigger a second
                        # update_build_config call for the "tool" field after this response,
                        # so we must populate the options here.
                        # 在此处直接获取工具，而不是延迟到前端回调
                        # 前端没有可靠的机制在响应后触发第二次 update_build_config 调用
                        try:
                            self.tools, build_config["mcp_server"]["value"] = await self.update_tool_list(
                                mcp_server_value=field_value
                            )
                            build_config["tool"]["options"] = [tool.name for tool in self.tools]
                            build_config["tool"]["placeholder"] = "Select a tool"
                        except (TimeoutError, asyncio.TimeoutError) as e:
                            msg = f"Timeout loading tools for MCP server: {e!s}"
                            await logger.awarning(msg)
                            build_config["tool"]["options"] = []
                            build_config["tool"]["placeholder"] = "Timeout on MCP server"
                        except (ValueError, ImportError, ConnectionError, OSError, RuntimeError) as e:
                            msg = f"Error loading tools for MCP server: {e!s}"
                            await logger.awarning(msg)
                            build_config["tool"]["options"] = []
                            build_config["tool"]["placeholder"] = "Error on MCP Server"
                    # Force a value refresh only when the user genuinely switched servers.
                    # server_changed is only True for real user-initiated changes (not initial load).
                    # 仅在用户实际切换服务器时强制刷新值
                    if server_changed:
                        build_config["tool"]["value"] = uuid.uuid4()
                else:
                    # Keep the tool dropdown hidden if in tool_mode
                    # 工具模式下保持工具下拉框隐藏
                    self._not_load_actions = True
                    build_config["tool"]["show"] = False

            elif field_name == "tool_mode":
                # 处理工具模式切换：tool_mode=True 时隐藏工具下拉框，直接通过输入参数调用
                build_config["tool"]["placeholder"] = ""
                build_config["tool"]["show"] = not bool(field_value) and bool(build_config["mcp_server"])
                self.remove_non_default_keys(build_config)
                self.tool = build_config["tool"]["value"]
                if field_value:
                    self._not_load_actions = True
                else:
                    build_config["tool"]["value"] = uuid.uuid4()
                    build_config["tool"]["show"] = True
                    # Fetch tools immediately instead of showing "Loading tools..."
                    # 立即获取工具列表，而不是显示 "Loading tools..."
                    try:
                        self.tools, build_config["mcp_server"]["value"] = await self.update_tool_list()
                        build_config["tool"]["options"] = [tool.name for tool in self.tools]
                        build_config["tool"]["placeholder"] = "Select a tool"
                    except (TimeoutError, asyncio.TimeoutError) as e:
                        msg = f"Timeout loading tools when toggling tool mode: {e!s}"
                        await logger.awarning(msg)
                        build_config["tool"]["options"] = []
                        build_config["tool"]["placeholder"] = "Timeout on MCP server"
                    except (ValueError, ImportError, ConnectionError, OSError, RuntimeError) as e:
                        msg = f"Error loading tools when toggling tool mode: {e!s}"
                        await logger.awarning(msg)
                        build_config["tool"]["options"] = []
                        build_config["tool"]["placeholder"] = "Error on MCP Server"
            elif field_name == "tools_metadata":
                self._not_load_actions = False

        except Exception as e:
            msg = f"Error in update_build_config: {e!s}"
            await logger.aexception(msg)
            raise ValueError(msg) from e
        else:
            return build_config

    @staticmethod
    def _unwrap_optional_annotation(annotation: Any) -> Any:
        """从联合类型注解中移除 None 分支（解包 Optional 类型）。

        例如：Optional[int] -> int，Union[str, None] -> str
        """
        # Remove a single None branch from a union annotation.
        # 从联合类型注解中移除单个 None 分支
        if isinstance(annotation, UnionType):
            non_none = [item for item in get_args(annotation) if item is not type(None)]
            if len(non_none) == 1:
                return non_none[0]
            return annotation

        if get_origin(annotation) is None:
            return annotation

        non_none = [item for item in get_args(annotation) if item is not type(None)]
        if len(non_none) == 1 and len(non_none) != len(get_args(annotation)):
            return non_none[0]
        return annotation

    @classmethod
    def _is_object_like_annotation(cls, annotation: Any) -> bool:
        """判断注解是否表示类似字典的载荷类型。

        返回 True 表示注解是 dict 或 BaseModel 的子类。
        """
        # Return True when the annotation represents a dict-like payload.
        # 当注解表示类似字典的载荷时返回 True
        annotation = cls._unwrap_optional_annotation(annotation)
        origin = get_origin(annotation)
        if origin is dict:
            return True
        return annotation is dict or (isinstance(annotation, type) and issubclass(annotation, BaseModel))

    @classmethod
    def _should_include_tool_argument(cls, model_field: Any, value: Any) -> bool:
        """判断工具参数是否应该被包含在调用参数中。

        省略空的可选值，以保持 MCP 服务器的默认值不变。
        """
        # Omit blank optional values so MCP server defaults remain intact.
        # 省略空的可选值，以保持 MCP 服务器的默认值完整
        if value is None:
            return False

        if model_field.is_required():
            return True

        if isinstance(value, str) and value == "":
            return False

        return not (
            value == {} and model_field.default is None and cls._is_object_like_annotation(model_field.annotation)
        )

    def _build_tool_kwargs(self, args_schema: type[BaseModel]) -> dict[str, Any]:
        """从组件输入中收集工具调用的关键字参数。

        省略空的可选值，仅包含非空参数。
        """
        # Collect tool kwargs from component inputs, omitting blank optional values.
        # 从组件输入中收集工具关键字参数，省略空的可选值
        kwargs: dict[str, Any] = {}
        for arg_name, model_field in args_schema.model_fields.items():
            value = getattr(self, arg_name, None)
            if isinstance(value, Message):
                value = value.text

            if self._should_include_tool_argument(model_field, value):
                kwargs[arg_name] = value

        return kwargs

    def get_inputs_for_all_tools(self, tools: list) -> dict:
        """获取所有工具的输入 schema。

        Returns:
            字典，键为工具名，值为对应的 Langflow 输入列表
        """
        # Get input schemas for all tools.
        # 获取所有工具的输入 schema
        inputs = {}
        for tool in tools:
            if not tool or not hasattr(tool, "name"):
                continue
            try:
                langflow_inputs = schema_to_langflow_inputs(tool.args_schema)
                inputs[tool.name] = langflow_inputs
            except (AttributeError, ValueError, TypeError, KeyError) as e:
                msg = f"Error getting inputs for tool {getattr(tool, 'name', 'unknown')}: {e!s}"
                logger.exception(msg)
                continue
        return inputs

    def remove_non_default_keys(self, build_config: dict) -> None:
        """从构建配置中移除非默认键（动态添加的工具输入参数）。"""
        # Remove non-default keys from the build config.
        # 从构建配置中移除非默认键
        for key in list(build_config.keys()):
            if key not in self.default_keys:
                build_config.pop(key)

    async def _update_tool_config(self, build_config: dict, tool_name: str) -> None:
        """更新工具配置，包括加载工具的输入参数 schema 到构建配置中。

        处理流程：
        1. 如果工具列表为空则先刷新
        2. 保存当前工具输入的已有值
        3. 清除所有非默认的动态输入
        4. 加载选中工具的新输入 schema
        5. 恢复之前保存的值（如果参数名匹配）

        Args:
            build_config: 构建配置字典
            tool_name: 选中的工具名称
        """
        # Update tool configuration with proper error handling.
        # 更新工具配置，包含适当的错误处理
        if not self.tools:
            self.tools, build_config["mcp_server"]["value"] = await self.update_tool_list()

        if not tool_name:
            return

        tool_obj = next((tool for tool in self.tools if tool.name == tool_name), None)
        if not tool_obj:
            msg = f"Tool {tool_name} not found in available tools: {self.tools}"
            self.remove_non_default_keys(build_config)
            build_config["tool"]["value"] = ""
            await logger.awarning(msg)
            return

        try:
            # Store current values before removing inputs (only for the current tool)
            # 在清除输入前保存当前值（仅保留当前工具的值）
            current_values = {}
            for key, value in build_config.items():
                if key not in self.default_keys and isinstance(value, dict) and "value" in value:
                    current_values[key] = value["value"]

            # Remove ALL non-default keys (all previous tool inputs)
            # 清除所有非默认键（之前所有工具的输入）
            self.remove_non_default_keys(build_config)

            # Get and validate new inputs for the selected tool
            # 获取并验证选中工具的新输入参数
            self.schema_inputs = await self._validate_schema_inputs(tool_obj)
            if not self.schema_inputs:
                msg = f"No input parameters to configure for tool '{tool_name}'"
                await logger.ainfo(msg)
                return

            # Add new inputs to build config for the selected tool only
            # 仅为选中的工具添加新输入到构建配置
            for schema_input in self.schema_inputs:
                if not schema_input or not hasattr(schema_input, "name"):
                    msg = "Invalid schema input detected, skipping"
                    await logger.awarning(msg)
                    continue

                try:
                    name = schema_input.name
                    input_dict = schema_input.to_dict()
                    input_dict.setdefault("value", None)
                    input_dict.setdefault("required", True)

                    build_config[name] = input_dict

                    # Preserve existing value if the parameter name exists in current_values
                    if name in current_values:
                        build_config[name]["value"] = current_values[name]

                except (AttributeError, KeyError, TypeError) as e:
                    msg = f"Error processing schema input {schema_input}: {e!s}"
                    await logger.aexception(msg)
                    continue
        except ValueError as e:
            msg = f"Schema validation error for tool {tool_name}: {e!s}"
            await logger.aexception(msg)
            self.schema_inputs = []
            return
        except (AttributeError, KeyError, TypeError) as e:
            msg = f"Error updating tool config: {e!s}"
            await logger.aexception(msg)
            raise ValueError(msg) from e

    async def build_output(self) -> DataFrame:
        """Build output with improved error handling and validation."""
        try:
            self.tools, _ = await self.update_tool_list()
            if self.tool != "":
                # Set session context for persistent MCP sessions using Langflow session ID
                session_context = self._get_session_context()
                if session_context:
                    self.stdio_client.set_session_context(session_context)
                    self.streamable_http_client.set_session_context(session_context)
                exec_tool = self._tool_cache[self.tool]
                kwargs = self._build_tool_kwargs(exec_tool.args_schema)
                unflattened_kwargs = maybe_unflatten_dict(kwargs)

                output = await exec_tool.coroutine(**unflattened_kwargs)
                tool_content = []
                for item in output.content:
                    item_dict = item.model_dump()
                    item_dict = self.process_output_item(item_dict)
                    tool_content.append(item_dict)

                if isinstance(tool_content, list) and all(isinstance(x, dict) for x in tool_content):
                    return DataFrame(tool_content)
                return DataFrame(data=tool_content)
            return DataFrame(data=[{"error": "You must select a tool"}])
        except Exception as e:
            msg = f"Error in build_output: {e!s}"
            await logger.aexception(msg)
            raise ValueError(msg) from e

    def process_output_item(self, item_dict):
        """Process the output of a tool."""
        if item_dict.get("type") == "text":
            text = item_dict.get("text")
            try:
                parsed = json.loads(text)
                # Ensure we always return a dictionary for DataFrame compatibility
                if isinstance(parsed, dict):
                    return parsed
                # Wrap non-dict parsed values in a dictionary
                return {"text": text, "parsed_value": parsed, "type": "text"}  # noqa: TRY300
            except json.JSONDecodeError:
                return item_dict
        return item_dict

    def _get_session_context(self) -> str | None:
        """Get the Langflow session ID for MCP session caching."""
        # Try to get session ID from the component's execution context
        if hasattr(self, "graph") and hasattr(self.graph, "session_id"):
            session_id = self.graph.session_id
            # Include server name to ensure different servers get different sessions
            server_name = ""
            mcp_server = getattr(self, "mcp_server", None)
            if isinstance(mcp_server, dict):
                server_name = mcp_server.get("name", "")
            elif mcp_server:
                server_name = str(mcp_server)
            return f"{session_id}_{server_name}" if session_id else None
        return None

    async def _get_tools(self):
        """Get cached tools or update if necessary."""
        mcp_server = getattr(self, "mcp_server", None)
        if not self._not_load_actions:
            tools, _ = await self.update_tool_list(mcp_server)
            return tools
        return []
