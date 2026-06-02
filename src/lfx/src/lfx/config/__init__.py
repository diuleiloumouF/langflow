"""lfx 配置模块 — Langflow CLI 命令的环境解析。

lfx configuration — environment resolution for Langflow CLI commands.
"""

# 从 environments 子模块导入配置相关的核心类型和函数
from lfx.config.environments import ConfigError, LangflowEnvironment, resolve_environment

# 模块公开接口：错误类型、环境类、环境解析函数
__all__ = ["ConfigError", "LangflowEnvironment", "resolve_environment"]
