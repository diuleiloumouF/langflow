# 从 lfx.log 导入日志配置和日志记录器
from lfx.log.logger import configure, logger

# 在模块级别暴露日志方法，以保持向后兼容性
info = logger.info
debug = logger.debug
warning = logger.warning
error = logger.error
critical = logger.critical
exception = logger.exception

# 在模块级别暴露异步日志方法
aerror = logger.aerror
ainfo = logger.ainfo
adebug = logger.adebug
awarning = logger.awarning
acritical = logger.acritical
aexception = logger.aexception

# 模块公开的 API 列表
__all__ = [
    "acritical",
    "adebug",
    "aerror",
    "aexception",
    "ainfo",
    "awarning",
    "configure",
    "critical",
    "debug",
    "error",
    "exception",
    "info",
    "logger",
    "warning",
]
