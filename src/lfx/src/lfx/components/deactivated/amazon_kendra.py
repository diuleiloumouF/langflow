# mypy: disable-error-code="attr-defined"
# Amazon Kendra 检索器的 LangChain 集成
from langchain_community.retrievers import AmazonKendraRetriever

# 缓存检查装饰器
from lfx.base.vectorstores.model import check_cached_vector_store

# 自定义组件基类
from lfx.custom.custom_component.custom_component import CustomComponent

# 输入组件类型
from lfx.io import DictInput, IntInput, StrInput


# Amazon Kendra 检索器组件，使用 Amazon Kendra API 进行文档检索
class AmazonKendraRetrieverComponent(CustomComponent):
    display_name: str = "Amazon Kendra Retriever"
    description: str = "Retriever that uses the Amazon Kendra API."
    name = "AmazonKendra"
    icon = "Amazon"
    legacy = True

    # 输入参数定义
    inputs = [
        # Kendra 索引 ID
        StrInput(
            name="index_id",
            display_name="Index ID",
        ),
        # AWS 区域名称
        StrInput(
            name="region_name",
            display_name="Region Name",
        ),
        # AWS 凭证配置文件名称
        StrInput(
            name="credentials_profile_name",
            display_name="Credentials Profile Name",
        ),
        # 属性过滤器
        DictInput(
            name="attribute_filter",
            display_name="Attribute Filter",
        ),
        # 返回的最相关结果数量
        IntInput(
            name="top_k",
            display_name="Top K",
            value=3,
        ),
        # 用户上下文信息
        DictInput(
            name="user_context",
            display_name="User Context",
        ),
    ]

    # 构建 Amazon Kendra 检索器实例
    @check_cached_vector_store
    def build_vector_store(self) -> AmazonKendraRetriever:
        """Builds the Amazon Kendra Retriever."""
        try:
            from langchain_community.retrievers import AmazonKendraRetriever
        except ImportError as e:
            msg = "Could not import AmazonKendraRetriever. Please install it with `pip install langchain-community`."
            raise ImportError(msg) from e

        try:
            output = AmazonKendraRetriever(
                index_id=self.index_id,
                top_k=self.top_k,
                region_name=self.region_name,
                credentials_profile_name=self.credentials_profile_name,
                attribute_filter=self.attribute_filter,
                user_context=self.user_context,
            )
        except Exception as e:
            msg = "Could not connect to AmazonKendra API."
            raise ValueError(msg) from e

        return output
