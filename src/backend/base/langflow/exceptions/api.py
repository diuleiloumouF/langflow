from fastapi import HTTPException
from pydantic import BaseModel

from langflow.api.utils import get_suggestion_message
from langflow.services.database.models.flow.model import Flow
from langflow.services.database.models.flow.utils import get_outdated_components


class InvalidChatInputError(Exception):
    """无效的聊天输入错误"""


# 工作流执行错误的基类
class WorkflowExecutionError(Exception):
    """Base exception for workflow execution errors."""


# 工作流执行超时错误
class WorkflowTimeoutError(WorkflowExecutionError):
    """Workflow execution timeout."""


# 工作流验证错误（例如：无效的流程数据、图构建失败）
class WorkflowValidationError(WorkflowExecutionError):
    """Workflow validation error (e.g., invalid flow data, graph build failure)."""


# 后台任务队列已满时抛出的错误
class WorkflowQueueFullError(WorkflowExecutionError):
    """Raised when the background task queue is full."""


# 服务器内存或其他资源不足时抛出的错误
class WorkflowResourceError(WorkflowExecutionError):
    """Raised when the server is out of memory or other resources."""


# 任务队列服务不可用时抛出的错误（例如：broker 宕机）
class WorkflowServiceUnavailableError(WorkflowExecutionError):
    """Raised when the task queue service is unavailable (e.g., broker down)."""


# create a pidantic documentation for this class
# 异常响应体模型，用于序列化异常信息返回给客户端
class ExceptionBody(BaseModel):
    # 错误消息，支持单条字符串或多条消息列表
    message: str | list[str]
    # 错误追踪信息（堆栈跟踪），可选
    traceback: str | list[str] | None = None
    # 错误描述信息，可选
    description: str | list[str] | None = None
    # 错误代码，可选
    code: str | None = None
    # 修复建议，可选，支持多条建议
    suggestion: str | list[str] | None = None


class APIException(HTTPException):
    """API 异常类，封装异常信息并生成结构化的错误响应体"""

    def __init__(self, exception: Exception, flow: Flow | None = None, status_code: int = 500):
        """初始化 API 异常

        Args:
            exception: 原始异常对象
            flow: 关联的流程对象，可选，用于检测过期组件
            status_code: HTTP 状态码，默认 500
        """
        body = self.build_exception_body(exception, flow)
        super().__init__(status_code=status_code, detail=body.model_dump_json())

    @staticmethod
    def build_exception_body(exc: str | list[str] | Exception, flow: Flow | None) -> ExceptionBody:
        """构建异常响应体

        将异常信息转换为结构化的 ExceptionBody 对象，
        如果关联了流程对象，还会检测过期组件并生成修复建议。

        Args:
            exc: 异常信息，可以是字符串、字符串列表或异常对象
            flow: 关联的流程对象，可选

        Returns:
            ExceptionBody: 结构化的异常响应体
        """
        body = {"message": str(exc)}
        if flow:
            # 检测流程中是否存在过期组件
            outdated_components = get_outdated_components(flow)
            if outdated_components:
                # 根据过期组件生成修复建议消息
                body["suggestion"] = get_suggestion_message(outdated_components)
        return ExceptionBody(**body)
