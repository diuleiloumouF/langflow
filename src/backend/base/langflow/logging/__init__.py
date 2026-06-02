# 从 lfx.log 导入日志配置和日志记录器
from lfx.log.logger import configure, logger

# 从本地 setup 模块导入日志启用/禁用函数
from .setup import disable_logging, enable_logging

# 模块公开的 API 列表
__all__ = ["configure", "disable_logging", "enable_logging", "logger"]
