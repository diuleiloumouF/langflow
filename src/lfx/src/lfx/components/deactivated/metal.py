# mypy: disable-error-code="attr-defined"
# Metal 检索器的 LangChain 集成
from langchain_community.retrievers import MetalRetriever

# 缓存检查装饰器
from lfx.base.vectorstores.model import check_cached_vector_store

# 自定义组件基类
from lfx.custom.custom_component.custom_component import CustomComponent

# 输入组件类型
from lfx.io import DictInput, SecretStrInput, StrInput


# Metal 检索器组件，使用 Metal API 进行文档检索
class MetalRetrieverComponent(CustomComponent):
    display_name: str = "Metal Retriever"
    description: str = "Retriever that uses the Metal API."
    name = "MetalRetriever"
    legacy = True

    # 输入参数定义
    inputs = [
        # Metal API 密钥
        SecretStrInput(
            name="api_key",
            display_name="Metal Retriever API Key",
            required=True,
        ),
        SecretStrInput(
            name="client_id",
            display_name="Client ID",
            required=True,
        ),
        StrInput(
            name="index_id",
            display_name="Index ID",
            required=True,
        ),
        DictInput(
            name="params",
            display_name="Parameters",
            required=False,
        ),
    ]

    @check_cached_vector_store
    def build_vector_store(self) -> MetalRetriever:
        """Builds the Metal Retriever."""
        try:
            from langchain_community.retrievers import MetalRetriever
            from metal_sdk.metal import Metal
        except ImportError as e:
            msg = "Could not import Metal. Please install it with `pip install metal-sdk langchain-community`."
            raise ImportError(msg) from e

        try:
            metal = Metal(api_key=self.api_key, client_id=self.client_id, index_id=self.index_id)
        except Exception as e:
            msg = "Could not connect to Metal API."
            raise ValueError(msg) from e

        return MetalRetriever(client=metal, params=self.params or {})
