from enum import Enum

# 服务类型枚举模块，定义了可注册到服务管理器的所有服务类型


# Enum for the different types of services that can be registered with the service manager.
class ServiceType(str, Enum):
    """Enum for the different types of services that can be registered with the service manager.

    可注册到服务管理器的不同类型服务的枚举。
    """

    # 认证服务 - 处理用户身份验证和授权
    AUTH_SERVICE = "auth_service"
    # 缓存服务 - 提供数据缓存能力
    CACHE_SERVICE = "cache_service"
    # 共享组件缓存服务 - 跨实例共享的组件缓存
    SHARED_COMPONENT_CACHE_SERVICE = "shared_component_cache_service"
    # 配置服务 - 管理全局设置和配置项
    SETTINGS_SERVICE = "settings_service"
    # 数据库服务 - 提供数据库连接和操作能力
    DATABASE_SERVICE = "database_service"
    # 聊天服务 - 处理聊天交互相关功能
    CHAT_SERVICE = "chat_service"
    # 会话服务 - 管理用户会话状态
    SESSION_SERVICE = "session_service"
    # 任务服务 - 后台任务调度和执行
    TASK_SERVICE = "task_service"
    # 应用商店服务 - 管理组件市场和商店功能
    STORE_SERVICE = "store_service"
    # 变量服务 - 管理用户自定义变量
    VARIABLE_SERVICE = "variable_service"
    # 存储服务 - 提供文件和对象存储能力
    STORAGE_SERVICE = "storage_service"
    # 状态服务 - 管理应用和流程的运行状态
    STATE_SERVICE = "state_service"
    # 追踪服务 - 记录流程执行的追踪和日志信息
    TRACING_SERVICE = "tracing_service"
    # 遥测服务 - 收集匿名使用数据和统计信息
    TELEMETRY_SERVICE = "telemetry_service"
    # 作业队列服务 - 管理异步任务队列
    JOB_QUEUE_SERVICE = "job_queue_service"
    # MCP 组合器服务 - 处理 MCP (Model Context Protocol) 相关功能
    MCP_COMPOSER_SERVICE = "mcp_composer_service"
    # 作业服务 - 管理独立的后台作业
    JOB_SERVICE = "jobs_service"
    # 流程事件服务 - 处理流程运行中的事件通知和分发
    FLOW_EVENTS_SERVICE = "flow_events_service"
