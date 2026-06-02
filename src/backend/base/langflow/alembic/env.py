# Alembic 数据库迁移环境配置文件
# 该文件定义了数据库迁移的运行环境，包括离线模式和在线模式

import asyncio
import hashlib
import os
from logging.config import fileConfig
from typing import Any

from alembic import context
from lfx.log.logger import logger
from sqlalchemy import pool, text
from sqlalchemy.event import listen
from sqlalchemy.ext.asyncio import async_engine_from_config

from langflow.services.database.service import SQLModel

# Alembic 配置对象，提供对 .ini 文件中值的访问
config = context.config

# 为 Python 日志记录解释配置文件
# 此行基本上设置了日志记录器
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 命名约定，用于自动生成迁移脚本中的约束名称
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
# 在此添加模型的 MetaData 对象，用于 'autogenerate' 支持
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata
target_metadata.naming_convention = NAMING_CONVENTION
# 配置中的其他值，由 env.py 的需求定义，可以获取：
# my_important_option = config.get_main_option("my_important_option")
# ... 等等。


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # 在离线模式下运行迁移
    # 此模式仅使用 URL 配置上下文，不需要创建 Engine
    # 通过跳过 Engine 创建，甚至不需要 DBAPI 可用
    url = config.get_main_option("sqlalchemy.url")
    configure_kwargs = {
        "url": url,
        "target_metadata": target_metadata,
        "literal_binds": True,
        "dialect_opts": {"paramstyle": "named"},
        "render_as_batch": True,
    }

    # 仅对 PostgreSQL 添加 prepare_threshold 设置
    if url and "postgresql" in url:
        configure_kwargs["prepare_threshold"] = None

    context.configure(**configure_kwargs)

    with context.begin_transaction():
        context.run_migrations()


def _sqlite_do_connect(
    dbapi_connection,
    connection_record,  # noqa: ARG001
):
    # 禁用 pysqlite 发送 BEGIN 语句
    # 同时阻止在任何 DDL 之前发送 COMMIT
    dbapi_connection.isolation_level = None


def _sqlite_do_begin(conn):
    # 发送自定义的 BEGIN 语句
    conn.exec_driver_sql("PRAGMA busy_timeout = 60000")
    conn.exec_driver_sql("BEGIN EXCLUSIVE")


def _do_run_migrations(connection):
    # 执行实际的数据库迁移操作
    configure_kwargs = {
        "connection": connection,
        "target_metadata": target_metadata,
        "render_as_batch": True,
    }

    # 仅对 PostgreSQL 添加 prepare_threshold 设置
    if connection.dialect.name == "postgresql":
        configure_kwargs["prepare_threshold"] = None

    context.configure(**configure_kwargs)
    with context.begin_transaction():
        if connection.dialect.name == "postgresql":
            # 如果提供了环境变量，则使用该命名空间，否则使用默认的静态密钥
            namespace = os.getenv("LANGFLOW_MIGRATION_LOCK_NAMESPACE")
            if namespace:
                lock_key = int(hashlib.sha256(namespace.encode()).hexdigest()[:16], 16) % (2**63 - 1)
                logger.info(f"Using migration lock namespace: {namespace}, lock_key: {lock_key}")
            else:
                lock_key = 11223344
                logger.info(f"Using default migration lock_key: {lock_key}")

            # 设置锁超时和获取 PostgreSQL 咨询锁，防止并发迁移
            connection.execute(text("SET LOCAL lock_timeout = '180s';"))
            connection.execute(text(f"SELECT pg_advisory_xact_lock({lock_key});"))
        context.run_migrations()


async def _run_async_migrations() -> None:
    # 禁用 PostgreSQL 的预处理语句（PgBouncer 兼容性所需）
    # SQLite 不支持此参数，因此仅为 PostgreSQL 添加
    config_section = config.get_section(config.config_ini_section, {})
    db_url = config_section.get("sqlalchemy.url", "")

    connect_args: dict[str, Any] = {}
    if db_url and "postgresql" in db_url:
        connect_args["prepare_threshold"] = None

    # 创建异步数据库引擎
    connectable = async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    if connectable.dialect.name == "sqlite":
        # SQLite 需要特殊的事件监听器来处理序列化隔离和事务性 DDL
        # 参见 https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
        listen(connectable.sync_engine, "connect", _sqlite_do_connect)
        listen(connectable.sync_engine, "begin", _sqlite_do_begin)

    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)

    # 释放引擎连接池资源
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # 在线模式下运行迁移
    # 此模式需要创建 Engine 并将连接与上下文关联
    asyncio.run(_run_async_migrations())


# 根据 Alembic 运行模式选择迁移方式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
