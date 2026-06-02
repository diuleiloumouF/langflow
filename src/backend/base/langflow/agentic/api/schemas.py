"""Request and response schemas for the Assistant API.

Assistant API 的请求和响应 schema 定义。
"""

from typing import Literal

from pydantic import BaseModel, Field

# All possible step types for SSE progress events
# SSE 进度事件的所有可能步骤类型
StepType = Literal[
    "generating",  # LLM is generating response
    # LLM 正在生成响应
    "generating_component",  # LLM is generating component code
    # LLM 正在生成组件代码
    "generation_complete",  # LLM finished generating
    # LLM 完成生成
    "extracting_code",  # Extracting Python code from response
    # 从响应中提取 Python 代码
    "validating",  # Validating component code
    # 正在验证组件代码
    "validated",  # Validation succeeded
    # 验证成功
    "validation_failed",  # Validation failed
    # 验证失败
    "retrying",  # About to retry with error context
    # 即将携带错误上下文进行重试
]


class AssistantRequest(BaseModel):
    """Request model for assistant interactions."""

    """Assistant 交互的请求模型。"""

    # 流程 ID，用于标识目标流程
    flow_id: str
    # 组件 ID，可选，用于指定目标组件
    component_id: str | None = None
    # 字段名称，可选，用于指定目标字段
    field_name: str | None = None
    # 输入值，可选，最大长度 2000 字符
    input_value: str | None = Field(None, max_length=2000)
    # 最大重试次数，可选，范围 1-5
    max_retries: int | None = Field(None, ge=1, le=5)
    # 模型名称，可选，用于指定使用的 LLM 模型
    model_name: str | None = None
    # 提供商名称，可选，用于指定模型提供商
    provider: str | None = None
    # 会话 ID，可选，用于标识对话会话
    session_id: str | None = None


class ValidationResult(BaseModel):
    """Result of component code validation."""

    """组件代码验证的结果模型。"""

    # 验证是否通过
    is_valid: bool
    # 验证通过后的代码，失败时为 None
    code: str | None = None
    # 错误信息，验证通过时为 None
    error: str | None = None
    # 组件类名，验证通过时返回
    class_name: str | None = None
