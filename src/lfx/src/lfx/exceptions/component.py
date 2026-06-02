from lfx.schema.properties import Source


class ComponentBuildError(Exception):
    """组件构建异常，当组件在构建过程中发生错误时抛出"""

    def __init__(self, message: str, formatted_traceback: str):
        # 错误消息
        self.message = message
        # 格式化的回溯信息，用于调试
        self.formatted_traceback = formatted_traceback
        super().__init__(message)


class StreamingError(Exception):
    """流式处理异常，当流式操作发生错误时抛出"""

    def __init__(self, cause: Exception, source: Source):
        # 导致异常的原始原因
        self.cause = cause
        # 异常来源标识，用于追踪错误来源
        self.source = source
        super().__init__(cause)
