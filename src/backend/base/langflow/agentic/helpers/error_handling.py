"""Error handling and categorization for the Assistant API."""
# Assistant API 的错误处理与分类模块

# 错误信息截断的最大长度（字符数）
MAX_ERROR_MESSAGE_LENGTH = 150
# 有意义的子串的最小长度，低于此长度的子串会被忽略
MIN_MEANINGFUL_PART_LENGTH = 10

# 错误模式匹配列表：每个元素为 (关键词列表, 对应的友好提示消息)
# 用于将技术性 API 错误转换为用户可读的提示信息
ERROR_PATTERNS: list[tuple[list[str], str]] = [
    (
        ["rate_limit", "rate limit", "429", "consumption_limit"],
        "Rate limit exceeded. Please wait a moment and try again.",
    ),
    (["authentication", "api_key", "unauthorized", "401"], "Authentication failed. Check your API key."),
    (["quota", "billing", "insufficient"], "API quota exceeded. Please check your account billing."),
    (["timeout", "timed out"], "Request timed out. Please try again."),
    (["connection", "network"], "Connection error. Please check your network and try again."),
    (["500", "internal server error"], "Server error. Please try again later."),
]


def extract_friendly_error(error_msg: str) -> str:
    """Convert technical API errors into user-friendly messages."""
    # 将错误信息转为小写以便模式匹配
    error_lower = error_msg.lower()

    # Pydantic schema validation errors — checked BEFORE the generic pattern loop
    # so a message like "HTTPException 500: 1 validation error for InputSchema..."
    # is not masked by the "500" → "Server error" fallback.
    # Pydantic schema 校验错误 — 在通用模式匹配之前检查，
    # 避免类似 "HTTPException 500: 1 validation error for InputSchema..."
    # 这样的消息被 "500" → "Server error" 的兜底规则误匹配
    schema_error_terms = ("validation error for", "input should be a valid", "pydantic.validationerror")
    if any(term in error_lower for term in schema_error_terms):
        return (
            "The selected model produced output that didn't match the expected schema. "
            "Try again or use a more capable model."
        )

    # 遍历预定义的错误模式，匹配后返回对应的友好消息
    for patterns, friendly_message in ERROR_PATTERNS:
        if any(pattern in error_lower or pattern in error_msg for pattern in patterns):
            return friendly_message

    # 模型不存在或不可用的错误提示
    model_missing_terms = ("not found", "does not exist", "not available")
    if "model" in error_lower and any(term in error_lower for term in model_missing_terms):
        return "Model not available. Please select a different model."

    # 内容安全策略拦截的错误提示
    if "content" in error_lower and any(term in error_lower for term in ["filter", "policy", "safety"]):
        return "Request blocked by content policy. Please modify your prompt."

    # 以上规则都不匹配时，截断原始错误信息后返回
    return _truncate_error_message(error_msg)


def _truncate_error_message(error_msg: str) -> str:
    """Truncate long error messages, preserving meaningful content."""
    # 错误信息未超长，直接返回原文
    if len(error_msg) <= MAX_ERROR_MESSAGE_LENGTH:
        return error_msg

    # 尝试按冒号分割，提取第一个有意义的子串返回
    if ":" in error_msg:
        for part in error_msg.split(":"):
            stripped = part.strip()
            if MIN_MEANINGFUL_PART_LENGTH < len(stripped) < MAX_ERROR_MESSAGE_LENGTH:
                return stripped

    # 无法提取有意义子串时，截断并添加省略号
    return f"{error_msg[:MAX_ERROR_MESSAGE_LENGTH]}..."
