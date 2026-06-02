# 带有可用模型元数据的扩展嵌入类
"""Extended embeddings class with available models metadata."""

from langchain_core.embeddings import Embeddings


# 支持多模型的嵌入包装类
class EmbeddingsWithModels(Embeddings):
    """Extended Embeddings class that includes available models with dedicated instances.

    This class inherits from LangChain Embeddings and provides a mapping of model names
    to their dedicated embedding instances, enabling multi-model support without the need
    for dynamic model switching.

    Attributes:
        embeddings: The primary LangChain Embeddings instance (used as fallback).
        available_models: Dict mapping model names to their dedicated Embeddings instances.
                         Each model has its own pre-configured instance with specific parameters.
    """

    # 主嵌入实例（作为默认/回退使用）
    # embeddings: Embeddings
    # 可用模型字典，将模型名称映射到各自的嵌入实例
    # available_models: dict[str, Embeddings]

    def __init__(
        self,
        embeddings: Embeddings,
        available_models: dict[str, Embeddings] | None = None,
    ):
        """Initialize the EmbeddingsWithModels wrapper.

        Args:
            embeddings: The primary LangChain Embeddings instance (used as default/fallback).
            available_models: Dict mapping model names to dedicated Embeddings instances.
                            Each value should be a fully configured Embeddings object ready to use.
                            Defaults to empty dict if not provided.
        """
        # 调用父类初始化方法
        super().__init__()
        # 设置主嵌入实例
        self.embeddings = embeddings
        # 设置可用模型映射，未提供时使用空字典
        self.available_models = available_models if available_models is not None else {}

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed search docs by delegating to the underlying embeddings instance.

        Args:
            texts: List of text to embed.

        Returns:
            List of embeddings.
        """
        # 委托给底层嵌入实例处理文档嵌入
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed query text by delegating to the underlying embeddings instance.

        Args:
            text: Text to embed.

        Returns:
            Embedding.
        """
        # 委托给底层嵌入实例处理查询嵌入
        return self.embeddings.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Asynchronously embed search docs.

        Args:
            texts: List of text to embed.

        Returns:
            List of embeddings.
        """
        # 异步委托给底层嵌入实例处理文档嵌入
        return await self.embeddings.aembed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        """Asynchronously embed query text.

        Args:
            text: Text to embed.

        Returns:
            Embedding.
        """
        # 异步委托给底层嵌入实例处理查询嵌入
        return await self.embeddings.aembed_query(text)

    def __call__(self, *args, **kwargs):
        """Make the class callable by delegating to the underlying embeddings instance.

        This handles cases where the embeddings object is used as a callable.

        Args:
            *args: Positional arguments to pass to the underlying embeddings instance.
            **kwargs: Keyword arguments to pass to the underlying embeddings instance.

        Returns:
            The result of calling the underlying embeddings instance.
        """
        # 支持将嵌入对象作为可调用对象使用
        if callable(self.embeddings):
            return self.embeddings(*args, **kwargs)
        msg = f"'{type(self.embeddings).__name__}' object is not callable"
        raise TypeError(msg)

    def __getattr__(self, name: str):
        """Delegate attribute access to the underlying embeddings instance.

        This ensures full compatibility with any additional methods or attributes
        that the underlying embeddings instance might have.

        Args:
            name: The attribute name to access.

        Returns:
            The attribute from the underlying embeddings instance.
        """
        # 代理属性访问到底层嵌入实例，确保与底层实例的完整兼容性
        return getattr(self.embeddings, name)

    def __repr__(self) -> str:
        """Return string representation of the wrapper."""
        # 返回包装类的字符串表示
        return f"EmbeddingsWithModels(embeddings={self.embeddings!r}, available_models={self.available_models!r})"
