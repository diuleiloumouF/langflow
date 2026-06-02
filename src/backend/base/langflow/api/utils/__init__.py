"""API utilities for Langflow.

This module provides backward compatibility by re-exporting all utilities
from the core module. This ensures existing imports continue to work while
allowing for better code organization.
"""

# Langflow API 工具函数模块。
# 该模块通过重新导出核心模块中的所有工具函数来提供向后兼容性，
# 确保现有的导入方式继续可用，同时支持更好的代码组织结构。

# Re-export everything from core and flow_utils modules to maintain backward compatibility
# 从核心模块和流程工具模块重新导出所有内容，以保持向后兼容性
from langflow.api.utils.core import (
    API_WORDS,  # API 相关关键词集合，用于判断请求是否包含 API 术语
    MAX_PAGE_SIZE,  # 分页查询的最大页面大小
    MIN_PAGE_SIZE,  # 分页查询的最小页面大小
    CurrentActiveMCPUser,  # 当前活跃的 MCP（模型上下文协议）用户的依赖注入类型
    CurrentActiveUser,  # 当前活跃用户的依赖注入类型
    DbSession,  # 可读写的数据库会话类型别名
    DbSessionReadOnly,  # 只读数据库会话类型别名
    EventDeliveryType,  # 事件投递类型枚举（如 SSE、轮询等）
    ValidatedFileName,  # 经过验证的文件名类型
    ValidatedFolderName,  # 经过验证的文件夹名类型
    build_input_keys_response,  # 构建输入键响应数据
    check_langflow_version,  # 检查 Langflow 版本是否匹配
    custom_params,  # 自定义参数依赖注入
    extract_global_variables_from_headers,  # 从请求头中提取全局变量
    format_elapsed_time,  # 格式化耗时显示
    format_exception_message,  # 格式化异常消息为用户友好的文本
    format_syntax_error_message,  # 格式化语法错误消息，附带行号等上下文信息
    get_causing_exception,  # 获取异常链中的根本原因异常
    get_is_component_from_data,  # 从数据中判断是否为组件类型
    get_suggestion_message,  # 根据异常类型生成修复建议消息
    get_top_level_vertices,  # 获取图中顶层（无入边）的顶点列表
    has_api_terms,  # 判断请求路径或参数中是否包含 API 相关术语
    normalize_code_for_import,  # 将用户代码标准化为可导入格式
    normalize_flow_for_export,  # 将流程数据标准化为可导出格式
    parse_exception,  # 解析异常对象为结构化的错误信息
    parse_value,  # 解析字符串值为对应的 Python 类型
    raise_error_if_astra_cloud_env,  # 在 Astra Cloud 环境下抛出限制性错误
    remove_api_keys,  # 从数据中移除 API 密钥等敏感信息
    validate_is_component,  # 验证给定数据是否为合法的组件
)
from langflow.api.utils.flow_utils import (
    build_and_cache_graph_from_data,  # 从数据构建图并缓存结果
    build_graph_from_data,  # 从流程数据构建可执行的图对象
    build_graph_from_db,  # 从数据库加载流程并构建图（带缓存）
    build_graph_from_db_no_cache,  # 从数据库加载流程并构建图（不使用缓存）
    cascade_delete_flow,  # 级联删除流程及其关联的所有数据
    scope_session_to_namespace,  # 将数据库会话限定到指定的命名空间
    verify_public_flow_and_get_user,  # 验证流程是否为公开流程并获取所属用户信息
)

# Explicitly list the main exports for better IDE support and documentation
# 显式列出主要导出项，便于 IDE 自动补全和文档生成
__all__ = [
    # Constants
    # 常量
    "API_WORDS",
    "MAX_PAGE_SIZE",
    "MIN_PAGE_SIZE",
    "CurrentActiveMCPUser",
    # Type annotations
    # 类型注解
    "CurrentActiveUser",
    "DbSession",
    "DbSessionReadOnly",
    # Enums
    # 枚举类型
    "EventDeliveryType",
    "ValidatedFileName",
    "ValidatedFolderName",
    "build_and_cache_graph_from_data",
    "build_graph_from_data",
    "build_graph_from_db",
    "build_graph_from_db_no_cache",
    "build_input_keys_response",
    "cascade_delete_flow",
    "check_langflow_version",
    "custom_params",
    "extract_global_variables_from_headers",
    "format_elapsed_time",
    "format_exception_message",
    "format_syntax_error_message",
    "get_causing_exception",
    "get_is_component_from_data",
    "get_suggestion_message",
    "get_top_level_vertices",
    # Functions
    # 工具函数
    "has_api_terms",
    "normalize_code_for_import",
    "normalize_flow_for_export",
    "parse_exception",
    "parse_value",
    "raise_error_if_astra_cloud_env",
    "remove_api_keys",
    "scope_session_to_namespace",
    "validate_is_component",
    "verify_public_flow_and_get_user",
]
