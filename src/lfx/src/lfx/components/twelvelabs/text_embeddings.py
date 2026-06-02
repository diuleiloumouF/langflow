"""TwelveLabs 文本嵌入组件。

该模块提供基于 TwelveLabs API 的文本嵌入功能，
用于将文本转换为向量表示。
"""

from twelvelabs import TwelveLabs

from lfx.base.embeddings.model import LCEmbeddingsModel
from lfx.field_typing import Embeddings
from lfx.io import DropdownInput, FloatInput, IntInput, SecretStrInput


class TwelveLabsTextEmbeddings(Embeddings):
    """TwelveLabs 文本嵌入实现类。

    封装 TwelveLabs API，提供文档嵌入和查询嵌入功能。
    继承自 Embeddings 基类，兼容 Langflow 的嵌入接口。
    """

    def __init__(self, api_key: str, model: str) -> None:
        """初始化 TwelveLabs 客户端。

        Args:
            api_key: TwelveLabs API 密钥，用于身份验证
            model: 嵌入模型名称，如 "Marengo-retrieval-2.7"
        """
        self.client = TwelveLabs(api_key=api_key)
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """将多个文档文本转换为嵌入向量。

        Args:
            texts: 待嵌入的文档文本列表

        Returns:
            嵌入向量列表，每个向量为浮点数列表
        """
        all_embeddings: list[list[float]] = []
        for text in texts:
            # 跳过空文本
            if not text:
                continue

            result = self.client.embed.create(model_name=self.model, text=text)

            if result.text_embedding and result.text_embedding.segments:
                for segment in result.text_embedding.segments:
                    all_embeddings.append([float(x) for x in segment.embeddings_float])
                    break  # Only take first segment for now  # 当前仅取第一个片段

        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        """将单个查询文本转换为嵌入向量。

        Args:
            text: 待嵌入的查询文本

        Returns:
            嵌入向量，为浮点数列表；若无结果则返回空列表
        """
        result = self.client.embed.create(model_name=self.model, text=text)

        if result.text_embedding and result.text_embedding.segments:
            return [float(x) for x in result.text_embedding.segments[0].embeddings_float]
        return []


class TwelveLabsTextEmbeddingsComponent(LCEmbeddingsModel):
    """TwelveLabs 文本嵌入 Langflow 组件。

    在 Langflow 画布上提供 TwelveLabs 文本嵌入功能的可视化组件，
    用户可通过界面配置 API 密钥和模型参数。
    """

    # 组件显示名称
    display_name = "TwelveLabs Text Embeddings"
    # 组件描述信息
    description = "Generate embeddings using TwelveLabs text embedding models."
    # 组件图标
    icon = "TwelveLabs"
    # 组件内部标识名
    name = "TwelveLabsTextEmbeddings"
    # 组件文档链接
    documentation = "https://github.com/twelvelabs-io/twelvelabs-developer-experience/blob/main/integrations/Langflow/TWELVE_LABS_COMPONENTS_README.md"

    # 组件输入参数定义
    inputs = [
        SecretStrInput(name="api_key", display_name="TwelveLabs API Key", value="TWELVELABS_API_KEY", required=True),
        DropdownInput(
            name="model",
            display_name="Model",
            advanced=False,
            # 可选模型列表
            options=["Marengo-retrieval-2.7"],
            value="Marengo-retrieval-2.7",
        ),
        # 最大重试次数，高级参数
        IntInput(name="max_retries", display_name="Max Retries", value=3, advanced=True),
        # 请求超时时间，高级参数
        FloatInput(name="request_timeout", display_name="Request Timeout", advanced=True),
    ]

    def build_embeddings(self) -> Embeddings:
        """构建并返回 TwelveLabs 文本嵌入实例。

        Returns:
            配置好的 TwelveLabsTextEmbeddings 实例
        """
        return TwelveLabsTextEmbeddings(api_key=self.api_key, model=self.model)
