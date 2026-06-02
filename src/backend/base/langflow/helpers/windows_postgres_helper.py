"""Helper for Windows + PostgreSQL event loop configuration."""
# Windows + PostgreSQL 事件循环配置辅助模块
# 在 Windows 平台使用 PostgreSQL 时，需要将事件循环策略切换为 WindowsSelectorEventLoopPolicy，
# 以确保 psycopg（PostgreSQL 驱动）的兼容性。

import asyncio
import os
import platform

from lfx.log.logger import logger

# 数据库连接 URL 的环境变量名
LANGFLOW_DATABASE_URL = "LANGFLOW_DATABASE_URL"
# PostgreSQL 连接 URL 的常见前缀
POSTGRESQL_PREFIXES = ("postgresql", "postgres")


# 配置 Windows 平台下 PostgreSQL 兼容的事件循环策略
def configure_windows_postgres_event_loop(source: str | None = None) -> bool:
    """Configure event loop for Windows + PostgreSQL compatibility.

    Args:
        source: Optional identifier for logging context

    Returns:
        True if configuration was applied, False otherwise
    """
    # 非 Windows 平台无需配置，直接返回
    if platform.system() != "Windows":
        return False

    # 从环境变量读取数据库连接 URL，检查是否使用 PostgreSQL
    db_url = os.environ.get(LANGFLOW_DATABASE_URL, "")
    if not db_url or not any(db_url.startswith(prefix) for prefix in POSTGRESQL_PREFIXES):
        return False

    # Use getattr to safely access the Windows-only class on all platforms
    selector_policy = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if selector_policy is None:
        return False

    # 获取当前事件循环策略，如果已经是 Selector 策略则无需切换
    current_policy = asyncio.get_event_loop_policy()
    if isinstance(current_policy, selector_policy):
        return False

    # 将事件循环策略切换为 WindowsSelectorEventLoopPolicy，以兼容 psycopg
    asyncio.set_event_loop_policy(selector_policy())

    # 构建日志上下文信息，记录事件循环切换的原因
    log_context = {"event_loop": "WindowsSelectorEventLoop", "reason": "psycopg_compatibility"}
    if source:
        log_context["source"] = source

    logger.debug("Windows PostgreSQL event loop configured", extra=log_context)
    return True
