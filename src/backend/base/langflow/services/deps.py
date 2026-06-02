from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Union

from langflow.services.schema import ServiceType

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免循环依赖
    from collections.abc import AsyncGenerator

    from sqlmodel.ext.asyncio.session import AsyncSession

    from langflow.services.cache.service import AsyncBaseCacheService, CacheService
    from langflow.services.chat.service import ChatService
    from langflow.services.database.service import DatabaseService
    from langflow.services.session.service import SessionService
    from langflow.services.state.service import StateService
    from langflow.services.store.service import StoreService
    from langflow.services.task.service import TaskService
    from langflow.services.tracing.service import TracingService
    from langflow.services.variable.service import VariableService

# 这些导入必须在 TYPE_CHECKING 之外，因为 FastAPI 使用 eval_str=True 来评估类型注解，
# 这些类型被用作 FastAPI 在模块加载时评估的依赖函数的返回类型。
from lfx.services.auth.base import BaseAuthService  # noqa: TC002
from lfx.services.settings.service import SettingsService  # noqa: TC002

from langflow.services.job_queue.service import JobQueueService  # noqa: TC001
from langflow.services.storage.service import StorageService  # noqa: TC001
from langflow.services.telemetry.service import TelemetryService  # noqa: TC001


def get_service(service_type: ServiceType, default=None):
    """检索给定服务类型的服务实例。

    Retrieves the service instance for the given service type.

    Args:
        service_type (ServiceType): The type of service to retrieve.
        default (ServiceFactory, optional): The default ServiceFactory to use if the service is not found.
            Defaults to None.

    Returns:
        Any: The service instance.

    """
    # 获取全局服务管理器实例
    from lfx.services.manager import get_service_manager

    service_manager = get_service_manager()

    if not service_manager.are_factories_registered():
        # 这是一个变通方法，确保服务管理器已初始化（非最优方案，但目前有效）
        # ! This is a workaround to ensure that the service manager is initialized
        # ! Not optimal, but it works for now
        from langflow.services.manager import ServiceManager

        service_manager.register_factories(ServiceManager.get_factories())
    return service_manager.get(service_type, default)


def get_telemetry_service() -> TelemetryService:
    """从服务管理器获取遥测服务实例。

    Retrieves the TelemetryService instance from the service manager.

    Returns:
        TelemetryService: The TelemetryService instance.
    """
    from langflow.services.telemetry.factory import TelemetryServiceFactory

    return get_service(ServiceType.TELEMETRY_SERVICE, TelemetryServiceFactory())


def get_tracing_service() -> TracingService:
    """从服务管理器获取追踪服务实例。

    Retrieves the TracingService instance from the service manager.

    Returns:
        TracingService: The TracingService instance.
    """
    from langflow.services.tracing.factory import TracingServiceFactory

    return get_service(ServiceType.TRACING_SERVICE, TracingServiceFactory())


def get_state_service() -> StateService:
    """从服务管理器获取状态服务实例。

    Retrieves the StateService instance from the service manager.

    Returns:
        The StateService instance.
    """
    from langflow.services.state.factory import StateServiceFactory

    return get_service(ServiceType.STATE_SERVICE, StateServiceFactory())


def get_storage_service() -> StorageService:
    """获取存储服务实例。

    Retrieves the storage service instance.

    Returns:
        The storage service instance.
    """
    from langflow.services.storage.factory import StorageServiceFactory

    return get_service(ServiceType.STORAGE_SERVICE, default=StorageServiceFactory())


def get_variable_service() -> VariableService:
    """Retrieves the VariableService instance from the service manager.

    Returns:
        The VariableService instance.

    """
    from langflow.services.variable.factory import VariableServiceFactory

    return get_service(ServiceType.VARIABLE_SERVICE, VariableServiceFactory())


def is_settings_service_initialized() -> bool:
    """Check if the SettingsService is already initialized without triggering initialization.

    Returns:
        bool: True if the SettingsService is already initialized, False otherwise.
    """
    from lfx.services.manager import get_service_manager

    return ServiceType.SETTINGS_SERVICE in get_service_manager().services


def get_settings_service() -> SettingsService:
    """Retrieves the SettingsService instance.

    If the service is not yet initialized, it will be initialized before returning.

    Returns:
        The SettingsService instance.

    Raises:
        ValueError: If the service cannot be retrieved or initialized.
    """
    from lfx.services.settings.factory import SettingsServiceFactory

    return get_service(ServiceType.SETTINGS_SERVICE, SettingsServiceFactory())


def get_db_service() -> DatabaseService:
    """Retrieves the DatabaseService instance from the service manager.

    Returns:
        The DatabaseService instance.

    """
    from langflow.services.database.factory import DatabaseServiceFactory

    return get_service(ServiceType.DATABASE_SERVICE, DatabaseServiceFactory())


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    msg = "get_session is deprecated, use session_scope instead"
    raise NotImplementedError(msg)


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for managing an async session scope.

    This context manager is used to manage an async session scope for database operations.
    It ensures that the session is properly committed if no exceptions occur,
    and rolled back if an exception is raised.

    Yields:
        AsyncSession: The async session object.

    Raises:
        Exception: If an error occurs during the session scope.

    """
    from lfx.services.deps import session_scope as lfx_session_scope

    async with lfx_session_scope() as session:
        yield session


def get_cache_service() -> Union[CacheService, AsyncBaseCacheService]:  # noqa: UP007
    """Retrieves the cache service from the service manager.

    Returns:
        The cache service instance.
    """
    from langflow.services.cache.factory import CacheServiceFactory

    return get_service(ServiceType.CACHE_SERVICE, CacheServiceFactory())


def get_shared_component_cache_service() -> CacheService:
    """Retrieves the cache service from the service manager.

    Returns:
        The cache service instance.
    """
    from langflow.services.shared_component_cache.factory import SharedComponentCacheServiceFactory

    return get_service(ServiceType.SHARED_COMPONENT_CACHE_SERVICE, SharedComponentCacheServiceFactory())


def get_session_service() -> SessionService:
    """Retrieves the session service from the service manager.

    Returns:
        The session service instance.
    """
    from langflow.services.session.factory import SessionServiceFactory

    return get_service(ServiceType.SESSION_SERVICE, SessionServiceFactory())


def get_task_service() -> TaskService:
    """Retrieves the TaskService instance from the service manager.

    Returns:
        The TaskService instance.

    """
    from langflow.services.task.factory import TaskServiceFactory

    return get_service(ServiceType.TASK_SERVICE, TaskServiceFactory())


def get_chat_service() -> ChatService:
    """Get the chat service instance.

    Returns:
        ChatService: The chat service instance.
    """
    return get_service(ServiceType.CHAT_SERVICE)


def get_store_service() -> StoreService:
    """Retrieves the StoreService instance from the service manager.

    Returns:
        StoreService: The StoreService instance.
    """
    return get_service(ServiceType.STORE_SERVICE)


def get_queue_service() -> JobQueueService:
    """Retrieves the QueueService instance from the service manager."""
    from langflow.services.job_queue.factory import JobQueueServiceFactory

    return get_service(ServiceType.JOB_QUEUE_SERVICE, JobQueueServiceFactory())


def get_auth_service() -> BaseAuthService:
    """Retrieve the authentication service."""
    from langflow.services.auth.factory import AuthServiceFactory

    return get_service(ServiceType.AUTH_SERVICE, AuthServiceFactory())


def get_job_service():
    """Retrieves the JobService instance from the service manager.

    Returns:
        JobService: The JobService instance.
    """
    from langflow.services.jobs.factory import JobServiceFactory

    return get_service(ServiceType.JOB_SERVICE, JobServiceFactory())


def get_flow_events_service():
    from langflow.services.flow_events.factory import FlowEventsServiceFactory

    return get_service(ServiceType.FLOW_EVENTS_SERVICE, FlowEventsServiceFactory())
