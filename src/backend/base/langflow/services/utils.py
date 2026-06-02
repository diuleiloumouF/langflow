from __future__ import annotations

import asyncio
from importlib import import_module
from typing import TYPE_CHECKING

from lfx.log.logger import logger
from lfx.services.settings.constants import DEFAULT_SUPERUSER, DEFAULT_SUPERUSER_PASSWORD
from lfx.services.settings.feature_flags import FEATURE_FLAGS
from sqlalchemy import delete
from sqlalchemy import exc as sqlalchemy_exc
from sqlmodel import col, select

from langflow.services.cache.base import ExternalAsyncBaseCacheService
from langflow.services.cache.factory import CacheServiceFactory
from langflow.services.database.models.transactions.model import TransactionTable
from langflow.services.database.models.vertex_builds.model import VertexBuildTable
from langflow.services.database.utils import initialize_database
from langflow.services.schema import ServiceType

from .deps import get_auth_service, get_db_service, get_service, get_settings_service, session_scope

if TYPE_CHECKING:
    from lfx.services.settings.manager import SettingsService
    from sqlmodel.ext.asyncio.session import AsyncSession


# 获取或创建超级用户，返回创建的用户对象，若超级用户已存在则返回 None
async def get_or_create_super_user(session: AsyncSession, username, password, is_default):
    from langflow.services.database.models.user.model import User

    # 查询数据库中是否存在指定用户名的用户
    stmt = select(User).where(User.username == username)
    result = await session.exec(stmt)
    user = result.first()

    auth = get_auth_service()
    if user and user.is_superuser:
        return None  # Superuser already exists

    if user and is_default:
        if user.is_superuser:
            if auth.verify_password(password, user.password):
                return None
            # Superuser exists but password is incorrect
            # which means that the user has changed the
            # base superuser credentials.
            # This means that the user has already created
            # a superuser and changed the password in the UI
            # so we don't need to do anything.
            await logger.adebug(
                "Superuser exists but password is incorrect. "
                "This means that the user has changed the "
                "base superuser credentials."
            )
            return None
        logger.debug("User with superuser credentials exists but is not a superuser.")
        return None

    if user:
        if auth.verify_password(password, user.password):
            msg = "User with superuser credentials exists but is not a superuser."
            raise ValueError(msg)
        msg = "Incorrect superuser credentials"
        raise ValueError(msg)

    if is_default:
        logger.debug("Creating default superuser.")
    else:
        logger.debug("Creating superuser.")
    return await auth.create_super_user(username, password, db=session)


# 设置超级用户：根据 AUTO_LOGIN 配置决定使用默认凭据还是自定义凭据
async def setup_superuser(settings_service: SettingsService, session: AsyncSession) -> None:
    if settings_service.auth_settings.AUTO_LOGIN:
        await logger.adebug("AUTO_LOGIN is set to True. Creating default superuser.")
        # 自动登录模式下使用默认超级用户名和密码
        username = DEFAULT_SUPERUSER
        password = DEFAULT_SUPERUSER_PASSWORD.get_secret_value()
    else:
        # Remove the default superuser if it exists
        await teardown_superuser(settings_service, session)
        # If AUTO_LOGIN is disabled, attempt to use configured credentials
        # or fall back to default credentials if none are provided.
        username = settings_service.auth_settings.SUPERUSER or DEFAULT_SUPERUSER
        password = (settings_service.auth_settings.SUPERUSER_PASSWORD or DEFAULT_SUPERUSER_PASSWORD).get_secret_value()

    if not username or not password:
        msg = "Username and password must be set"
        raise ValueError(msg)

    # 判断当前使用的是否是默认凭据
    is_default = (username == DEFAULT_SUPERUSER) and (password == DEFAULT_SUPERUSER_PASSWORD.get_secret_value())

    try:
        user = await get_or_create_super_user(
            session=session, username=username, password=password, is_default=is_default
        )
        if user is not None:
            await logger.adebug("Superuser created successfully.")
    except Exception as exc:
        logger.exception(exc)
        msg = "Could not create superuser. Please create a superuser manually."
        raise RuntimeError(msg) from exc
    finally:
        # Scrub credentials from in-memory settings after setup
        # 设置完成后清除内存中的凭据信息，避免泄露
        settings_service.auth_settings.reset_credentials()


# 拆除超级用户：在 AUTO_LOGIN 关闭时移除未登录过的默认超级用户
async def teardown_superuser(settings_service, session: AsyncSession) -> None:
    """Teardown the superuser."""
    # If AUTO_LOGIN is True, we will remove the default superuser
    # from the database.

    if not settings_service.auth_settings.AUTO_LOGIN:
        try:
            await logger.adebug("AUTO_LOGIN is set to False. Removing default superuser if exists.")
            username = DEFAULT_SUPERUSER
            from langflow.services.database.models.user.model import User

            stmt = select(User).where(User.username == username)
            result = await session.exec(stmt)
            user = result.first()
            # Check if super was ever logged in, if not delete it
            # if it has logged in, it means the user is using it to login
            # 仅当超级用户从未登录过时才删除，避免删除用户正在使用的账号
            if user and user.is_superuser is True and not user.last_login_at:
                await session.delete(user)
                await logger.adebug("Default superuser removed successfully.")

        except Exception as exc:
            logger.exception(exc)
            msg = "Could not remove default superuser."
            raise RuntimeError(msg) from exc


# 拆除所有服务：先拆除超级用户，再拆除服务管理器中的所有服务
async def teardown_services() -> None:
    """Teardown all the services."""
    async with session_scope() as session:
        await teardown_superuser(get_settings_service(), session)

    from lfx.services.manager import get_service_manager

    service_manager = get_service_manager()
    await service_manager.teardown()


# 初始化设置服务（Settings Service）
def initialize_settings_service() -> None:
    """Initialize the settings manager."""
    from lfx.services.settings import factory as settings_factory

    get_service(ServiceType.SETTINGS_SERVICE, settings_factory.SettingsServiceFactory())


# 初始化会话服务：依次初始化设置服务、缓存服务和会话服务
def initialize_session_service() -> None:
    """Initialize the session manager."""
    from langflow.services.cache import factory as cache_factory
    from langflow.services.session import factory as session_service_factory

    initialize_settings_service()

    get_service(
        ServiceType.CACHE_SERVICE,
        cache_factory.CacheServiceFactory(),
    )

    get_service(
        ServiceType.SESSION_SERVICE,
        session_service_factory.SessionServiceFactory(),
    )


# 清理旧事务记录：删除超过配置上限的最早事务
async def clean_transactions(settings_service: SettingsService, session: AsyncSession) -> None:
    """Clean up old transactions from the database.

    This function deletes transactions that exceed the maximum number to keep (configured in settings).
    It orders transactions by timestamp descending and removes the oldest ones beyond the limit.

    Args:
        settings_service: The settings service containing configuration like max_transactions_to_keep
        session: The database session to use for the deletion
    """
    try:
        # Delete transactions using bulk delete
        # 构建批量删除语句：选取超出保留数量的最旧事务 ID 进行删除
        delete_stmt = delete(TransactionTable).where(
            col(TransactionTable.id).in_(
                select(TransactionTable.id)
                .order_by(col(TransactionTable.timestamp).desc())
                .offset(settings_service.settings.max_transactions_to_keep)
            )
        )

        await session.exec(delete_stmt)
        logger.debug("Successfully cleaned up old transactions")
    except (sqlalchemy_exc.SQLAlchemyError, asyncio.TimeoutError) as exc:
        logger.error(f"Error cleaning up transactions: {exc!s}")
        # Don't re-raise since this is a cleanup task
        # 清理任务不应抛出异常，仅记录错误日志


# 清理旧的顶点构建记录：删除超过配置上限的最早构建记录
async def clean_vertex_builds(settings_service: SettingsService, session: AsyncSession) -> None:
    """Clean up old vertex builds from the database.

    This function deletes vertex builds that exceed the maximum number to keep (configured in settings).
    It orders vertex builds by timestamp descending and removes the oldest ones beyond the limit.

    Args:
        settings_service: The settings service containing configuration like max_vertex_builds_to_keep
        session: The database session to use for the deletion
    """
    try:
        # Delete vertex builds using bulk delete
        # 构建批量删除语句：选取超出保留数量的最旧顶点构建记录 ID 进行删除
        delete_stmt = delete(VertexBuildTable).where(
            col(VertexBuildTable.id).in_(
                select(VertexBuildTable.id)
                .order_by(col(VertexBuildTable.timestamp).desc())
                .offset(settings_service.settings.max_vertex_builds_to_keep)
            )
        )

        await session.exec(delete_stmt)
        logger.debug("Successfully cleaned up old vertex builds")
    except (sqlalchemy_exc.SQLAlchemyError, asyncio.TimeoutError) as exc:
        logger.error(f"Error cleaning up vertex builds: {exc!s}")
        # Don't re-raise since this is a cleanup task
        # 清理任务不应抛出异常，仅记录错误日志


# 注册所有内置服务工厂到服务管理器
def register_all_service_factories() -> None:
    """Register all available service factories with the service manager."""
    # Import all service factories
    from lfx.services.manager import get_service_manager
    from lfx.services.schema import ServiceType

    service_manager = get_service_manager()
    from lfx.services.mcp_composer import factory as mcp_composer_factory
    from lfx.services.settings import factory as settings_factory

    from langflow.services.auth import factory as auth_factory
    from langflow.services.auth.service import AuthService
    from langflow.services.cache import factory as cache_factory
    from langflow.services.chat import factory as chat_factory
    from langflow.services.database import factory as database_factory
    from langflow.services.job_queue import factory as job_queue_factory
    from langflow.services.session import factory as session_factory
    from langflow.services.shared_component_cache import factory as shared_component_cache_factory
    from langflow.services.state import factory as state_factory
    from langflow.services.storage import factory as storage_factory
    from langflow.services.store import factory as store_factory
    from langflow.services.task import factory as task_factory
    from langflow.services.telemetry import factory as telemetry_factory
    from langflow.services.tracing import factory as tracing_factory
    from langflow.services.transaction import factory as transaction_factory
    from langflow.services.variable import factory as variable_factory

    # Register all factories
    # 注册各个服务的工厂实例
    service_manager.register_factory(settings_factory.SettingsServiceFactory())
    service_manager.register_factory(cache_factory.CacheServiceFactory())
    service_manager.register_factory(chat_factory.ChatServiceFactory())
    service_manager.register_factory(database_factory.DatabaseServiceFactory())
    service_manager.register_factory(session_factory.SessionServiceFactory())
    service_manager.register_factory(storage_factory.StorageServiceFactory())
    service_manager.register_factory(variable_factory.VariableServiceFactory())
    service_manager.register_factory(telemetry_factory.TelemetryServiceFactory())
    service_manager.register_factory(tracing_factory.TracingServiceFactory())
    service_manager.register_factory(transaction_factory.TransactionServiceFactory())
    service_manager.register_factory(state_factory.StateServiceFactory())
    service_manager.register_factory(job_queue_factory.JobQueueServiceFactory())
    service_manager.register_factory(task_factory.TaskServiceFactory())
    service_manager.register_factory(store_factory.StoreServiceFactory())
    service_manager.register_factory(shared_component_cache_factory.SharedComponentCacheServiceFactory())
    # Override LFX's no-op auth service with Langflow's full JWT implementation
    # 用 Langflow 的完整 JWT 实现覆盖 LFX 的空操作认证服务
    service_manager.register_service_class(ServiceType.AUTH_SERVICE, AuthService, override=True)
    service_manager.register_factory(auth_factory.AuthServiceFactory())
    service_manager.register_factory(mcp_composer_factory.MCPComposerServiceFactory())
    service_manager.set_factory_registered()


# 注册内置适配器模块，触发 @register_adapter 装饰器的副作用
def register_builtin_adapters() -> None:
    """Import built-in adapter modules so ``@register_adapter`` decorators fire.

    Mirrors ``register_all_service_factories()`` for the adapter registry system.
    Each import triggers the ``@register_adapter`` decorator at module scope,
    registering the adapter class on the AdapterRegistry singleton.

    TODO: Watsonx risks are documented here because registration is runtime-optional:
    missing ``ibm_*`` modules should skip adapter registration, but broad
    ``ModuleNotFoundError`` handling can also hide internal import regressions.
    Future deployment API routing must treat "provider exists but adapter is not
    registered in this runtime" as an explicit, deterministic error path.
    Keep direct adapter imports limited to guarded paths and maintain CI
    coverage that confirms Watsonx tests run (not skip) in eligible environments.
    """
    if not FEATURE_FLAGS.wxo_deployments:
        logger.debug("Skipping deployment adapter registration: wxo_deployments feature flag disabled")
        return

    try:
        # 动态导入 Watsonx Orchestrate 适配器模块
        import_module("langflow.services.adapters.deployment.watsonx_orchestrate")
    except ModuleNotFoundError as exc:
        logger.info("Skipping Watsonx Orchestrate adapter registration: %s", exc)


# 注册内置部署映射器模块，触发模块级别的注册副作用
def register_builtin_deployment_mappers() -> None:
    """Import built-in deployment mapper modules so registration side effects fire."""
    if not FEATURE_FLAGS.wxo_deployments:
        logger.debug("Skipping deployment mapper registration: wxo_deployments feature flag disabled")
        return

    try:
        # 动态导入 Watsonx Orchestrate 部署映射器模块
        import_module("langflow.api.v1.mappers.deployments.watsonx_orchestrate")
    except ModuleNotFoundError as exc:
        logger.info("Skipping Watsonx Orchestrate deployment mapper registration: %s", exc)


# 初始化所有服务：注册工厂、测试缓存连接、初始化数据库、设置超级用户、清理旧数据
async def initialize_services(*, fix_migration: bool = False) -> None:
    """Initialize all the services needed."""
    from langflow.helpers.windows_postgres_helper import configure_windows_postgres_event_loop

    # 配置 Windows 环境下 PostgreSQL 的事件循环策略
    configure_windows_postgres_event_loop(source="initialize_services")

    # Register all service factories first
    # 注册所有服务工厂、适配器和部署映射器
    register_all_service_factories()
    register_builtin_adapters()
    register_builtin_deployment_mappers()

    cache_service = get_service(ServiceType.CACHE_SERVICE, default=CacheServiceFactory())
    # Test external cache connection
    # 如果使用外部缓存服务，测试连接是否成功
    if isinstance(cache_service, ExternalAsyncBaseCacheService) and not (await cache_service.is_connected()):
        msg = "Cache service failed to connect to external database"
        raise ConnectionError(msg)

    # Setup the superuser
    # 初始化数据库并设置超级用户
    await initialize_database(fix_migration=fix_migration)
    db_service = get_db_service()
    await db_service.initialize_alembic_log_file()
    async with session_scope() as session:
        settings_service = get_service(ServiceType.SETTINGS_SERVICE)
        await setup_superuser(settings_service, session)
    try:
        # 将无主的 flows 分配给超级用户
        await get_db_service().assign_orphaned_flows_to_superuser()
    except sqlalchemy_exc.IntegrityError as exc:
        await logger.awarning(f"Error assigning orphaned flows to the superuser: {exc!s}")

    # 清理超过保留上限的旧事务和旧顶点构建记录
    async with session_scope() as session:
        await clean_transactions(settings_service, session)
        await clean_vertex_builds(settings_service, session)
