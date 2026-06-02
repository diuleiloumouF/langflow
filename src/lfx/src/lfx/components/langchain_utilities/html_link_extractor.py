from typing import Any

from langchain_community.graph_vectorstores.extractors import HtmlLinkExtractor, LinkExtractorTransformer
from langchain_core.documents import BaseDocumentTransformer

from lfx.base.document_transformers.model import LCDocumentTransformerComponent
from lfx.inputs.inputs import BoolInput, DataInput, StrInput


# HTML 链接提取器组件，从 HTML 内容中提取超链接
# HTML link extractor component for extracting hyperlinks from HTML content
class HtmlLinkExtractorComponent(LCDocumentTransformerComponent):
    display_name = "HTML Link Extractor"
    description = "Extract hyperlinks from HTML content."
    documentation = "https://python.langchain.com/v0.2/api_reference/community/graph_vectorstores/langchain_community.graph_vectorstores.extractors.html_link_extractor.HtmlLinkExtractor.html"
    name = "HtmlLinkExtractor"
    icon = "LangChain"

    inputs = [
        StrInput(name="kind", display_name="Kind of edge", value="hyperlink", required=False),
        BoolInput(name="drop_fragments", display_name="Drop URL fragments", value=True, required=False),
        DataInput(
            name="data_input",
            display_name="Input",
            info="The texts from which to extract links.",
            input_types=["Document", "Data", "JSON"],
            required=True,
        ),
    ]

    # 获取数据输入
    def get_data_input(self) -> Any:
        return self.data_input

    # 构建文档转换器实例
    def build_document_transformer(self) -> BaseDocumentTransformer:
        return LinkExtractorTransformer(
            [HtmlLinkExtractor(kind=self.kind, drop_fragments=self.drop_fragments).as_document_extractor()]
        )
