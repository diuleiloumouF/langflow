"""LFX services module - pluggable service architecture for dependency injection."""

# 中文说明：LFX 服务模块 - 可插拔的服务架构，用于依赖注入

# 适配器注册与清理：注册适配器实例，以及清理所有适配器注册表
from .adapters.registry import register_adapter, teardown_all_adapter_registries

# 部署适配器获取：根据部署类型获取对应的部署适配器实例
from .deps import get_deployment_adapter

# 服务协议接口定义：各类服务遵循的协议（抽象接口），用于类型检查和依赖注入
from .interfaces import (
    AuthServiceProtocol,  # 认证服务协议
    CacheServiceProtocol,  # 缓存服务协议
    ChatServiceProtocol,  # 聊天服务协议
    DatabaseServiceProtocol,  # 数据库服务协议
    DeploymentServiceProtocol,  # 部署服务协议
    SettingsServiceProtocol,  # 设置服务协议
    StorageServiceProtocol,  # 存储服务协议
    TracingServiceProtocol,  # 链路追踪服务协议
    VariableServiceProtocol,  # 变量服务协议
)

# 服务管理器：统一管理所有服务实例的生命周期（创建、获取、销毁）
from .manager import ServiceManager

# MCP 组合服务：管理 MCP（Model Context Protocol）服务的组合与工厂创建
from .mcp_composer import MCPComposerService, MCPComposerServiceFactory

# 服务注册装饰器/函数：将服务类注册到全局服务注册表中
from .registry import register_service

# 空操作会话：用于不需要实际数据库会话的场景（如只读操作或测试）
from .session import NoopSession

# 公开 API：定义模块对外暴露的所有符号
__all__ = [
    "AuthServiceProtocol",  # 认证服务协议
    "CacheServiceProtocol",  # 缓存服务协议
    "ChatServiceProtocol",  # 聊天服务协议
    "DatabaseServiceProtocol",  # 数据库服务协议
    "DeploymentServiceProtocol",  # 部署服务协议
    "MCPComposerService",  # MCP 组合服务
    "MCPComposerServiceFactory",  # MCP 组合服务工厂
    "NoopSession",  # 空操作会话
    "ServiceManager",  # 服务管理器
    "SettingsServiceProtocol",  # 设置服务协议
    "StorageServiceProtocol",  # 存储服务协议
    "TracingServiceProtocol",  # 链路追踪服务协议
    "VariableServiceProtocol",  # 变量服务协议
    "get_deployment_adapter",  # 获取部署适配器
    "register_adapter",  # 注册适配器
    "register_service",  # 注册服务
    "teardown_all_adapter_registries",  # 清理所有适配器注册表
]
