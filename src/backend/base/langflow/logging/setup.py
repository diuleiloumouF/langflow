# 从 lfx.log 导入日志记录器
from lfx.log.logger import logger

# 标记日志是否已配置过
LOGGING_CONFIGURED = False


def disable_logging() -> None:
    """禁用 langflow 模块的日志输出。"""
    global LOGGING_CONFIGURED  # noqa: PLW0603
    # 仅在首次调用时禁用日志，避免重复操作
    if not LOGGING_CONFIGURED:
        logger.disable("langflow")
        LOGGING_CONFIGURED = True


def enable_logging() -> None:
    """启用 langflow 模块的日志输出。"""
    global LOGGING_CONFIGURED  # noqa: PLW0603
    # 启用 langflow 模块的日志
    logger.enable("langflow")
    LOGGING_CONFIGURED = True
