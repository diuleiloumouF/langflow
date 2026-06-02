# 从 Markdown 响应中提取 Python 代码的工具模块
"""Python code extraction from markdown responses."""

import re

# 匹配闭合的 Python 代码块（```python ... ```）
PYTHON_CODE_BLOCK_PATTERN = r"```python\s*([\s\S]*?)```"
# 匹配闭合的通用代码块（``` ... ```）
GENERIC_CODE_BLOCK_PATTERN = r"```\s*([\s\S]*?)```"
# 匹配未闭合的 Python 代码块（以 ```python 开头但没有结尾）
UNCLOSED_PYTHON_BLOCK_PATTERN = r"```python\s*([\s\S]*)$"
# 匹配未闭合的通用代码块（以 ``` 开头但没有结尾）
UNCLOSED_GENERIC_BLOCK_PATTERN = r"```\s*([\s\S]*)$"


def extract_python_code(text: str) -> str | None:
    # 从 Markdown 代码块中提取 Python 代码。
    # 支持闭合（```python ... ```）和未闭合的代码块。
    # 返回第一个看起来像 Langflow 组件的代码块。
    """Extract Python code from markdown code blocks.

    Handles both closed (```python ... ```) and unclosed blocks.
    Returns the first code block that appears to be a Langflow component.
    """
    matches = _find_code_blocks(text)
    if not matches:
        return None

    return _find_component_code(matches) or matches[0].strip()


def _find_code_blocks(text: str) -> list[str]:
    # 查找文本中的所有代码块，支持闭合和未闭合的代码块
    """Find all code blocks in text, handling both closed and unclosed blocks."""
    matches = re.findall(PYTHON_CODE_BLOCK_PATTERN, text, re.IGNORECASE)
    if matches:
        return matches

    matches = re.findall(GENERIC_CODE_BLOCK_PATTERN, text)
    if matches:
        return matches

    return _find_unclosed_code_block(text)


def _find_unclosed_code_block(text: str) -> list[str]:
    # 处理 LLM 响应中未用 ``` 闭合的代码块
    """Handle LLM responses that don't close the code block with ```."""
    for pattern in [UNCLOSED_PYTHON_BLOCK_PATTERN, UNCLOSED_GENERIC_BLOCK_PATTERN]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            code = match.group(1).rstrip("`").strip()
            return [code] if code else []

    return []


def _find_component_code(matches: list[str]) -> str | None:
    # 从匹配结果中查找第一个看起来像 Langflow 组件的代码
    """Find the first match that looks like a Langflow component."""
    for match in matches:
        if "class " in match and "Component" in match:
            return match.strip()
    return None


# 为了向后兼容而保留的别名
# Alias for backward compatibility
extract_component_code = extract_python_code
