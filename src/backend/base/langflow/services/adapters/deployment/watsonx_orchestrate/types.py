"""Watsonx Orchestrate 适配器的数据类 / Dataclasses for the Watsonx Orchestrate adapter.

`WxOClient` 在构造时即刻创建 SDK 客户端（`AgentClient`、`ToolClient`、
`ConnectionsClient` 和 `BaseWXOClient`），以确保在 ``asyncio.to_thread``
工作线程中访问时的线程安全性。

`WxOClient` eagerly creates SDK clients (`AgentClient`, `ToolClient`,
`ConnectionsClient`, and `BaseWXOClient`) at construction time to
guarantee thread safety when accessed from ``asyncio.to_thread`` workers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ibm_watsonx_orchestrate_clients.agents.agent_client import AgentClient
from ibm_watsonx_orchestrate_clients.common.base_client import BaseWXOClient
from ibm_watsonx_orchestrate_clients.connections.connections_client import ConnectionsClient
from ibm_watsonx_orchestrate_clients.tools.tool_client import ToolClient

if TYPE_CHECKING:
    # 仅在类型检查时导入认证器基类，避免运行时依赖
    from ibm_cloud_sdk_core.authenticators import Authenticator


@dataclass(frozen=True, slots=True)
class WxOClient:
    """具有即时 SDK 客户端初始化功能的提供者客户端门面。

    所有子客户端均在 ``__post_init__`` 中通过 ``instance_url``
    和 ``authenticator`` 构建，确保它们共享相同的 URL 和认证上下文。
    数据类设置为冻结状态以防止构建后对凭据的修改。
    """

    """Provider client facade with eager SDK client initialization.

    All sub-clients are constructed in ``__post_init__`` from ``instance_url``
    and ``authenticator`` so that they are guaranteed to share the same
    URL and authentication context. The dataclass is frozen to prevent
    post-construction mutation of credentials.
    """

    # IBM Cloud 实例的 URL 地址
    instance_url: str
    # IBM Cloud 认证器实例，用于身份验证
    authenticator: Authenticator
    # 基础客户端，提供通用 HTTP 方法（不参与 init/repr）
    base: BaseWXOClient = field(init=False, repr=False)
    # 工具客户端，用于管理工具相关操作（不参与 init/repr）
    tool: ToolClient = field(init=False, repr=False)
    # 连接客户端，用于管理连接相关操作（不参与 init/repr）
    connections: ConnectionsClient = field(init=False, repr=False)
    # 智能体客户端，用于管理智能体相关操作（不参与 init/repr）
    agent: AgentClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # 去除 URL 末尾的斜杠，统一格式
        url = self.instance_url.rstrip("/")
        # 验证 URL 不能为空
        if not url:
            msg = "instance_url must be a non-empty string."
            raise ValueError(msg)
        # 使用 object.__setattr__ 绕过冻结数据类的限制来设置属性
        # Use object.__setattr__ because the dataclass is frozen.
        object.__setattr__(self, "instance_url", url)
        # 初始化基础客户端
        object.__setattr__(self, "base", BaseWXOClient(base_url=url, authenticator=self.authenticator))
        # 初始化工具客户端
        object.__setattr__(self, "tool", ToolClient(base_url=url, authenticator=self.authenticator))
        # 初始化连接客户端
        object.__setattr__(self, "connections", ConnectionsClient(base_url=url, authenticator=self.authenticator))
        # 初始化智能体客户端
        object.__setattr__(self, "agent", AgentClient(base_url=url, authenticator=self.authenticator))

    # -- SDK 私有方法封装 ----------------------------------------------------------
    # 集中访问 SDK 内部的 _get/_post 方法，使 SDK 升级带来的变更
    # 仅需修改此文件即可。
    # -- SDK private-method wrappers ------------------------------------------
    # Centralise access to SDK-internal _get/_post so breakage from SDK
    # upgrades is confined to this single file.

    def get_agents_raw(self, params: dict[str, Any] | None = None) -> Any:
        """获取智能体列表的原始 API 响应。"""
        return self.base._get("/agents", params=params)  # noqa: SLF001

    def get_models_raw(self, params: dict[str, Any] | None = None) -> Any:
        """获取模型列表的原始 API 响应。"""
        return self.base._get("/models", params=params)  # noqa: SLF001

    def get_tools_raw(self, params: dict[str, Any] | None = None) -> Any:
        """获取工具列表的原始 API 响应。"""
        return self.base._get("/tools", params=params)  # noqa: SLF001

    def post_run(self, *, data: dict[str, Any]) -> Any:
        """提交一次运行请求，返回运行结果。"""
        return self.base._post("/runs", data=data)  # noqa: SLF001

    def get_run(self, run_id: str) -> Any:
        """根据运行 ID 获取运行状态和结果。"""
        return self.base._get(f"/runs/{run_id}")  # noqa: SLF001

    def upload_tool_artifact(self, tool_id: str, *, files: dict[str, Any]) -> Any:
        """上传工具制品文件到指定工具。"""
        return self.base._post(f"/tools/{tool_id}/upload", files=files)  # noqa: SLF001


@dataclass(frozen=True, slots=True)
class WxOCredentials:
    """Watsonx Orchestrate 凭据封装类，持有实例 URL 和认证器。"""

    # IBM Cloud 实例的 URL 地址
    instance_url: str
    # IBM Cloud 认证器，repr 中隐藏以避免泄露敏感信息
    authenticator: Authenticator = field(repr=False)

    def __post_init__(self) -> None:
        # 验证 URL 不能为空或仅包含空白字符
        if not self.instance_url or not self.instance_url.strip():
            msg = "instance_url must be a non-empty string."
            raise ValueError(msg)

    def __repr__(self) -> str:
        """自定义字符串表示，隐藏认证器详细信息，仅显示类名。"""
        return (
            f"WxOCredentials(instance_url={self.instance_url!r}, authenticator={self.authenticator.__class__.__name__})"
        )
