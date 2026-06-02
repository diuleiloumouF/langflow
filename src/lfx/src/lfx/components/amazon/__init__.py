from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 仅在类型检查时导入，避免运行时循环依赖和不必要的开销
if TYPE_CHECKING:
    from lfx.components.amazon.amazon_bedrock_embedding import AmazonBedrockEmbeddingsComponent
    from lfx.components.amazon.amazon_bedrock_model import AmazonBedrockComponent
    from lfx.components.amazon.s3_bucket_uploader import S3BucketUploaderComponent

# 动态导入映射表：组件类名 -> 对应模块名（不含扩展名）
_dynamic_imports = {
    "AmazonBedrockEmbeddingsComponent": "amazon_bedrock_embedding",
    "AmazonBedrockComponent": "amazon_bedrock_model",
    "S3BucketUploaderComponent": "s3_bucket_uploader",
}

# 模块公开导出的组件列表
__all__ = ["AmazonBedrockComponent", "AmazonBedrockEmbeddingsComponent", "S3BucketUploaderComponent"]


def __getattr__(attr_name: str) -> Any:
    """Lazily import amazon components on attribute access."""
    # 当模块属性被访问时，才按需导入对应的组件模块，提升启动性能
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 输出仅包含公开导出的组件名称
    return list(__all__)
