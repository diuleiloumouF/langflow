from typing import Any

from fastapi import HTTPException, status


# 序列化异常类，继承自 FastAPI 的 HTTPException，用于处理数据序列化为 JSON 时发生的错误
class SerializationError(HTTPException):
    """Exception raised when there are errors serializing data to JSON."""

    def __init__(
        self,
        detail: str,
        original_error: Exception | None = None,
        data: Any = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        # 保存原始异常信息，便于调试和日志追踪
        self.original_error = original_error
        # 保存导致序列化失败的原始数据
        self.data = data

    @classmethod
    def from_exception(cls, exc: Exception, data: Any = None) -> "SerializationError":
        """Create a SerializationError from an existing exception."""
        # 从原始异常中提取错误信息列表
        errors = exc.args[0] if exc.args else []

        # 如果错误信息是列表，逐个检查错误类型并提供针对性的提示
        if isinstance(errors, list):
            for error in errors:
                if isinstance(error, TypeError):
                    # 检测协程未 await 的情况
                    if "'coroutine'" in str(error):
                        return cls(
                            detail=(
                                "The component contains async functions that need to be awaited. Please add 'await' "
                                "before any async function calls in your component code."
                            ),
                            original_error=exc,
                            data=data,
                        )
                    # 检测包含不可 JSON 序列化的对象（如自定义类实例）
                    if "vars()" in str(error):
                        return cls(
                            detail=(
                                "The component contains objects that cannot be converted to JSON. Please ensure all "
                                "properties and return values in your component are basic Python types like strings, "
                                "numbers, lists, or dictionaries."
                            ),
                            original_error=exc,
                            data=data,
                        )

        # Generic error for other cases
        # 对于其他未知的序列化错误，返回通用错误提示
        return cls(
            detail=(
                "The component returned invalid data. Please check that all values in your component (properties, "
                "return values, etc.) are basic Python types that can be converted to JSON."
            ),
            original_error=exc,
            data=data,
        )
