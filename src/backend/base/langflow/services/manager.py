"""Langflow ServiceManager - re-exports from lfx for backwards compatibility."""
# Langflow 服务管理器 - 从 lfx 重新导出以保持向后兼容性

from __future__ import annotations

# Re-export everything from lfx
# 从 lfx 重新导出所有内容，保持向后兼容
from lfx.services.manager import NoFactoryRegisteredError, ServiceManager, get_service_manager

# 模块公开导出的符号列表
__all__ = ["NoFactoryRegisteredError", "ServiceManager", "get_service_manager"]


def initialize_settings_service() -> None:
    """Initialize the settings manager."""
    # 初始化设置管理器
    # 从 lfx 导入设置服务工厂并注册到服务管理器
    from lfx.services.settings import factory as settings_factory

    get_service_manager().register_factory(settings_factory.SettingsServiceFactory())


def initialize_session_service() -> None:
    """Initialize the session manager."""
    # 初始化会话管理器
    # 先初始化设置服务，然后注册缓存服务和会话服务的工厂
    from langflow.services.cache import factory as cache_factory
    from langflow.services.session import factory as session_service_factory

    initialize_settings_service()

    get_service_manager().register_factory(cache_factory.CacheServiceFactory())
    get_service_manager().register_factory(session_service_factory.SessionServiceFactory())
