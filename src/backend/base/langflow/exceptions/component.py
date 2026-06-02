# 创建异常类，接收消息和格式化的追踪信息

# 创建一个接收消息和格式化追踪信息的异常类

from langflow.schema.properties import Source


class ComponentBuildError(Exception):
    # 组件构建错误异常，用于组件构建过程中的错误处理
    def __init__(self, message: str, formatted_traceback: str):
        # 错误消息
        self.message = message
        # 格式化的追踪信息
        self.formatted_traceback = formatted_traceback
        super().__init__(message)


class StreamingError(Exception):
    # 流式处理错误异常，用于流式传输过程中的错误处理
    def __init__(self, cause: Exception, source: Source):
        # 引发异常的原因
        self.cause = cause
        # 错误来源（用于定位问题）
        self.source = source
        super().__init__(cause)
