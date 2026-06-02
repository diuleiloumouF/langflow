"""Schema modules for lfx package."""
# lfx 包的 Schema 模块，定义了数据模型、请求/响应结构体以及序列化工具。

__all__ = [
    # 工作流相关的 HTTP 响应模型
    "WORKFLOW_EXECUTION_RESPONSES",
    "WORKFLOW_STATUS_RESPONSES",
    "ComponentOutput",
    # 核心数据类型
    "Data",
    "DataFrame",
    # 错误相关
    "ErrorDetail",
    # 输入值与调整参数
    "InputValue",
    "JobStatus",
    "Message",
    # OpenAI Responses API 相关的请求/响应模型
    "OpenAIErrorResponse",
    "OpenAIResponsesRequest",
    "OpenAIResponsesResponse",
    "OpenAIResponsesStreamChunk",
    "Tweaks",
    # 序列化工具
    "UUIDstr",
    # 工作流执行相关的请求/响应/事件模型
    "WorkflowExecutionRequest",
    "WorkflowExecutionResponse",
    "WorkflowJobResponse",
    "WorkflowStopRequest",
    "WorkflowStopResponse",
    "WorkflowStreamEvent",
    # OpenAI 错误构造辅助函数
    "create_openai_error",
    "create_openai_error_chunk",
    # 点号访问字典
    "dotdict",
]


def __getattr__(name: str):
    # Import to avoid circular dependencies
    # 使用延迟导入（lazy import）来避免循环依赖，仅在实际访问时才从子模块导入对应的符号。
    if name == "Data":
        from .data import Data

        return Data
    if name == "DataFrame":
        from .dataframe import DataFrame

        return DataFrame
    if name == "dotdict":
        from .dotdict import dotdict

        return dotdict
    if name == "InputValue":
        from .graph import InputValue

        return InputValue
    if name == "Tweaks":
        from .graph import Tweaks

        return Tweaks
    if name == "Message":
        from .message import Message

        return Message
    if name == "UUIDstr":
        from .serialize import UUIDstr

        return UUIDstr
    if name == "OpenAIResponsesRequest":
        from .openai_responses_schemas import OpenAIResponsesRequest

        return OpenAIResponsesRequest
    if name == "OpenAIResponsesResponse":
        from .openai_responses_schemas import OpenAIResponsesResponse

        return OpenAIResponsesResponse
    if name == "OpenAIResponsesStreamChunk":
        from .openai_responses_schemas import OpenAIResponsesStreamChunk

        return OpenAIResponsesStreamChunk
    if name == "OpenAIErrorResponse":
        from .openai_responses_schemas import OpenAIErrorResponse

        return OpenAIErrorResponse
    if name == "create_openai_error":
        from .openai_responses_schemas import create_openai_error

        return create_openai_error
    if name == "create_openai_error_chunk":
        from .openai_responses_schemas import create_openai_error_chunk

        return create_openai_error_chunk
    if name == "WorkflowExecutionRequest":
        from .workflow import WorkflowExecutionRequest

        return WorkflowExecutionRequest
    if name == "WorkflowExecutionResponse":
        from .workflow import WorkflowExecutionResponse

        return WorkflowExecutionResponse
    if name == "WorkflowJobResponse":
        from .workflow import WorkflowJobResponse

        return WorkflowJobResponse
    if name == "WorkflowStreamEvent":
        from .workflow import WorkflowStreamEvent

        return WorkflowStreamEvent
    if name == "WORKFLOW_EXECUTION_RESPONSES":
        from .workflow import WORKFLOW_EXECUTION_RESPONSES

        return WORKFLOW_EXECUTION_RESPONSES
    if name == "WORKFLOW_STATUS_RESPONSES":
        from .workflow import WORKFLOW_STATUS_RESPONSES

        return WORKFLOW_STATUS_RESPONSES
    if name == "WorkflowStopRequest":
        from .workflow import WorkflowStopRequest

        return WorkflowStopRequest
    if name == "WorkflowStopResponse":
        from .workflow import WorkflowStopResponse

        return WorkflowStopResponse
    if name == "JobStatus":
        from .workflow import JobStatus

        return JobStatus
    if name == "ErrorDetail":
        from .workflow import ErrorDetail

        return ErrorDetail
    if name == "ComponentOutput":
        from .workflow import ComponentOutput

        return ComponentOutput

    # 当访问的属性不在已知导出列表中时，抛出 AttributeError。
    msg = f"module '{__name__}' has no attribute '{name}'"
    raise AttributeError(msg)
