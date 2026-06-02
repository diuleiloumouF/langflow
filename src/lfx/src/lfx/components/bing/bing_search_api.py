# 类型转换工具
from typing import cast

# LangChain Bing 搜索工具和 API 封装
from langchain_community.tools.bing_search import BingSearchResults
from langchain_community.utilities import BingSearchAPIWrapper

# 工具组件基类、类型定义、输入组件、数据模型
from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import IntInput, MessageTextInput, MultilineInput, SecretStrInput
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.template.field.base import Output


# Bing 搜索 API 组件，用于调用 Bing 搜索接口获取搜索结果
class BingSearchAPIComponent(LCToolComponent):
    display_name = "Bing Search API"
    # 组件描述：调用 Bing 搜索 API
    description = "Call the Bing Search API."
    name = "BingSearchAPI"
    icon = "Bing"

    # 输入参数定义
    inputs = [
        # Bing 订阅密钥
        SecretStrInput(name="bing_subscription_key", display_name="Bing Subscription Key"),
        # 搜索关键词输入（多行文本）
        MultilineInput(
            name="input_value",
            display_name="Input",
        ),
        # 自定义 Bing 搜索 URL（可选）
        MessageTextInput(name="bing_search_url", display_name="Bing Search URL", advanced=True),
        # 返回结果数量
        IntInput(name="k", display_name="Number of results", value=4, required=True),
    ]

    # 输出参数：表格形式的搜索结果和可复用的搜索工具
    outputs = [
        Output(display_name="Table", name="dataframe", method="fetch_content_dataframe"),
        Output(display_name="Tool", name="tool", method="build_tool"),
    ]

    # 运行模型，返回搜索结果的 DataFrame
    def run_model(self) -> DataFrame:
        return self.fetch_content_dataframe()

    # 获取搜索内容并返回 Data 列表
    def fetch_content(self) -> list[Data]:
        if self.bing_search_url:
            wrapper = BingSearchAPIWrapper(
                bing_search_url=self.bing_search_url, bing_subscription_key=self.bing_subscription_key
            )
        else:
            wrapper = BingSearchAPIWrapper(bing_subscription_key=self.bing_subscription_key)
        results = wrapper.results(query=self.input_value, num_results=self.k)
        data = [Data(data=result, text=result["snippet"]) for result in results]
        self.status = data
        return data

    # 将搜索结果转换为 DataFrame 表格格式
    def fetch_content_dataframe(self) -> DataFrame:
        data = self.fetch_content()
        return DataFrame(data)

    # 构建并返回 Bing 搜索工具实例，供其他组件复用
    def build_tool(self) -> Tool:
        if self.bing_search_url:
            wrapper = BingSearchAPIWrapper(
                bing_search_url=self.bing_search_url, bing_subscription_key=self.bing_subscription_key
            )
        else:
            wrapper = BingSearchAPIWrapper(bing_subscription_key=self.bing_subscription_key)
        return cast("Tool", BingSearchResults(api_wrapper=wrapper, num_results=self.k))
