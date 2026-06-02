# Wikipedia 查询组件，通过 Wikipedia API 搜索和获取百科内容
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import BoolInput, IntInput, MessageTextInput, MultilineInput
from lfx.io import Output
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame


# Wikipedia 查询组件，调用 Wikipedia API 搜索并返回结构化数据
class WikipediaComponent(Component):
    # 组件显示名称
    display_name = "Wikipedia"
    # 组件描述
    description = "Call Wikipedia API."
    # 组件图标
    icon = "Wikipedia"

    # 组件输入参数定义
    inputs = [
        # 搜索查询内容（多行文本输入）
        MultilineInput(
            name="input_value",
            display_name="Input",
            tool_mode=True,
        ),
        # 搜索语言，默认为英语
        MessageTextInput(name="lang", display_name="Language", value="en"),
        # 返回的结果数量
        IntInput(name="k", display_name="Number of results", value=4, required=True),
        # 是否加载所有可用的元数据
        BoolInput(name="load_all_available_meta", display_name="Load all available meta", value=False, advanced=True),
        # 文档内容最大字符数
        IntInput(
            name="doc_content_chars_max", display_name="Document content characters max", value=4000, advanced=True
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(display_name="Table", name="dataframe", method="fetch_content_dataframe"),
    ]

    # 运行模型并返回 DataFrame 格式结果
    def run_model(self) -> DataFrame:
        return self.fetch_content_dataframe()

    # 构建 Wikipedia API 包装器实例
    def _build_wrapper(self) -> WikipediaAPIWrapper:
        return WikipediaAPIWrapper(
            top_k_results=self.k,
            lang=self.lang,
            load_all_available_meta=self.load_all_available_meta,
            doc_content_chars_max=self.doc_content_chars_max,
        )

    # 获取 Wikipedia 搜索内容
    def fetch_content(self) -> list[Data]:
        wrapper = self._build_wrapper()
        docs = wrapper.load(self.input_value)
        data = [Data.from_document(doc) for doc in docs]
        self.status = data
        return data

    # 将搜索内容转换为 DataFrame 格式
    def fetch_content_dataframe(self) -> DataFrame:
        data = self.fetch_content()
        return DataFrame(data)
