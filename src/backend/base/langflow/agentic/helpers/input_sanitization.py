"""输入净化和提示词注入检测模块。
安全功能：在用户输入到达大语言模型之前进行验证和净化。
检测提示词注入攻击、系统提示词泄露和角色劫持。

Input sanitization and prompt injection detection.

Security: Validates and sanitizes user input BEFORE it reaches the LLM.
Detects prompt injection attempts, system prompt leaking, and role hijacking.
"""

import re
from dataclasses import dataclass

# 最大输入长度限制，防止过长输入
MAX_INPUT_LENGTH = 2000

# 拒绝处理请求时返回的提示信息
REFUSAL_MESSAGE = (
    "I'm sorry, but I can't process that request. "
    "I'm the Langflow Assistant and I can help you with "
    "Langflow components, flows, and technical questions. "
    "Please rephrase your question about Langflow."
)

# 提示词注入检测模式：(编译后的正则表达式, 违规描述)
# 每个模式针对特定的注入技术
# 这些模式经过精心设计，避免对合法的 Langflow 问题产生误报（例如 "how do I ignore errors" 不会被标记为注入）
#
# Prompt injection patterns: (compiled_regex, violation_description)
# Each pattern targets a specific injection technique.
# Patterns are intentionally specific to avoid false positives on
# legitimate Langflow questions (e.g., "how do I ignore errors").
INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # 指令覆盖尝试：尝试让 AI 忽略之前的指令
    # Instruction override attempts
    (
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
        "Prompt injection: instruction override attempt",
    ),
    (
        re.compile(r"ignore\s+(all\s+)?above\s+instructions", re.IGNORECASE),
        "Prompt injection: instruction override attempt",
    ),
    (
        re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
        "Prompt injection: instruction override attempt",
    ),
    (
        re.compile(r"forget\s+(all\s+)?(previous|prior|your)\s+instructions", re.IGNORECASE),
        "Prompt injection: instruction override attempt",
    ),
    (
        re.compile(r"IMPORTANT:\s*new\s+instructions|OVERRIDE:", re.IGNORECASE),
        "Prompt injection: instruction override attempt",
    ),
    # 角色劫持尝试：尝试让 AI 扮演其他角色
    # Role hijacking attempts
    (
        re.compile(r"you\s+are\s+now\s+(a|an|my)\s+", re.IGNORECASE),
        "Prompt injection: role hijacking attempt",
    ),
    (
        re.compile(r"act\s+as\s+(a|an|if\s+you\s+were)\s+", re.IGNORECASE),
        "Prompt injection: role hijacking attempt",
    ),
    (
        re.compile(r"pretend\s+(you\s+are|to\s+be)\s+", re.IGNORECASE),
        "Prompt injection: role hijacking attempt",
    ),
    # 系统提示词提取尝试：尝试获取系统提示词内容
    # System prompt extraction attempts
    (
        re.compile(
            r"(reveal|show|print|output|repeat|display)\s+(your\s+)?(system\s+prompt|instructions|initial\s+prompt)",
            re.IGNORECASE,
        ),
        "Prompt injection: system prompt extraction attempt",
    ),
    (
        re.compile(
            r"what\s+(are|is)\s+your\s+(system\s+prompt|instructions|initial\s+prompt)",
            re.IGNORECASE,
        ),
        "Prompt injection: system prompt extraction attempt",
    ),
    # 原始提示词分隔符注入：尝试注入原始的提示词分隔符
    # Raw prompt delimiter injection
    (
        re.compile(r"\[SYSTEM\]|\[INST\]|<<SYS>>|<\|im_start\|>system", re.IGNORECASE),
        "Prompt injection: raw prompt delimiter injection",
    ),
]


@dataclass(frozen=True)
class SanitizationResult:
    """输入净化检查结果数据类。

    用于封装输入净化检查的结果，包含是否安全、净化后的输入和违规原因。

    Result of input sanitization check.
    """

    # 输入是否安全，True 表示通过检查
    is_safe: bool
    # 净化后的输入文本
    sanitized_input: str
    # 违规原因描述，None 表示没有违规
    violation: str | None = None


def sanitize_input(text: str) -> SanitizationResult:
    """验证并净化用户输入，防止提示词注入攻击。

    在用户输入到达大语言模型之前进行安全检查。
    检查提示词注入模式并规范化输入。
    如果检测到注入攻击，返回 is_safe=False 的 SanitizationResult。

    Validate and sanitize user input before it reaches the LLM.
    Checks for prompt injection patterns and normalizes the input.
    Returns a SanitizationResult with is_safe=False if injection is detected.
    """
    # 空输入直接返回安全结果
    if not text:
        return SanitizationResult(is_safe=True, sanitized_input="")

    # 检查是否存在注入模式
    violation = _check_injection_patterns(text)
    if violation:
        return SanitizationResult(is_safe=False, sanitized_input=text, violation=violation)

    # 对输入进行规范化处理
    normalized = _normalize_input(text)
    return SanitizationResult(is_safe=True, sanitized_input=normalized)


def _check_injection_patterns(text: str) -> str | None:
    """检查文本是否包含已知的提示词注入模式。

    返回第一个发现的违规描述，如果文本安全则返回 None。

    Check text against known prompt injection patterns.
    Returns the first violation description found, or None if clean.
    """
    for pattern, violation in INJECTION_PATTERNS:
        if pattern.search(text):
            return violation
    return None


def _normalize_input(text: str) -> str:
    """规范化输入：去除空白字符和空字节。

    清理输入文本，移除可能导致问题的特殊字符。

    Normalize input by stripping whitespace and removing null bytes.
    """
    # 移除空字节
    cleaned = text.replace("\x00", "")
    # 将多个空白字符合并为一个空格，并去除首尾空白
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # 截断到最大输入长度
    return cleaned[:MAX_INPUT_LENGTH]
