# 压缩器组件基类
from lfx.base.compressors.model import LCCompressorComponent

# 文档压缩器类型
from lfx.field_typing import BaseDocumentCompressor

# 输入组件类型
from lfx.inputs.inputs import SecretStrInput
from lfx.io import DropdownInput

# 输出字段定义
from lfx.template.field.base import Output


# Cohere 重排序组件，使用 Cohere API 对文档进行重新排序
class CohereRerankComponent(LCCompressorComponent):
    display_name = "Cohere Rerank"
    description = "Rerank documents using the Cohere API."
    name = "CohereRerank"
    icon = "Cohere"

    # 输入参数定义
    inputs = [
        # 继承父类的输入参数
        *LCCompressorComponent.inputs,
        # Cohere API 密钥
        SecretStrInput(
            name="api_key",
            display_name="Cohere API Key",
        ),
        # 重排序模型选择
        DropdownInput(
            name="model",
            display_name="Model",
            options=[
                "rerank-english-v3.0",
                "rerank-multilingual-v3.0",
                "rerank-english-v2.0",
                "rerank-multilingual-v2.0",
            ],
            value="rerank-english-v3.0",
        ),
    ]

    # 输出参数定义
    outputs = [
        Output(
            display_name="Reranked Documents",
            name="reranked_documents",
            method="compress_documents",
        ),
    ]

    # 构建 Cohere 重排序压缩器实例
    def build_compressor(self) -> BaseDocumentCompressor:  # type: ignore[type-var]
        try:
            from langchain_cohere import CohereRerank
        except ImportError as e:
            msg = "Please install langchain-cohere to use the Cohere model."
            raise ImportError(msg) from e
        return CohereRerank(
            cohere_api_key=self.api_key,
            model=self.model,
            top_n=self.top_n,
        )
