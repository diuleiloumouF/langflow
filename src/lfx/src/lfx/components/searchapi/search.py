from typing import Any

from langchain_community.utilities.searchapi import SearchApiAPIWrapper

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import DictInput, DropdownInput, IntInput, MultilineInput, SecretStrInput
from lfx.io import Output
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame


# 搜索组件：封装 SearchApi API，支持 Google、Bing、DuckDuckGo 搜索引擎
class SearchComponent(Component):
    display_name: str = "SearchApi"
    # 调用 SearchApi API 并限制结果数量，支持 Google、Bing 和 DuckDuckGo
    description: str = "Calls the SearchApi API with result limiting. Supports Google, Bing and DuckDuckGo."
    documentation: str = "https://www.searchapi.io/docs/google"
    icon = "SearchAPI"

    # 组件输入参数定义
    inputs = [
        # 搜索引擎选择下拉框，可选 google、bing、duckduckgo
        DropdownInput(name="engine", display_name="Engine", value="google", options=["google", "bing", "duckduckgo"]),
        # SearchApi API 密钥（必填）
        SecretStrInput(name="api_key", display_name="SearchAPI API Key", required=True),
        # 搜索输入内容（支持多行输入，工具模式下可用）
        MultilineInput(
            name="input_value",
            display_name="Input",
            tool_mode=True,
        ),
        # 额外的搜索参数（字典类型，高级选项）
        DictInput(name="search_params", display_name="Search parameters", advanced=True, is_list=True),
        # 最大返回结果数，默认为 5
        IntInput(name="max_results", display_name="Max Results", value=5, advanced=True),
        # 摘要文本的最大字符长度，默认为 100
        IntInput(name="max_snippet_length", display_name="Max Snippet Length", value=100, advanced=True),
    ]

    # 组件输出定义：将搜索结果以表格（DataFrame）形式返回
    outputs = [
        Output(display_name="Table", name="dataframe", method="fetch_content_dataframe"),
    ]

    # 构建 SearchApi API 封装对象
    def _build_wrapper(self):
        return SearchApiAPIWrapper(engine=self.engine, searchapi_api_key=self.api_key)

    # 模型运行入口，委托给 fetch_content_dataframe 返回 DataFrame
    def run_model(self) -> DataFrame:
        return self.fetch_content_dataframe()

    # 执行搜索并返回结构化的搜索结果列表
    def fetch_content(self) -> list[Data]:
        wrapper = self._build_wrapper()

        # 内部搜索函数：执行查询并按参数限制结果数量和摘要长度
        def search_func(
            query: str, params: dict[str, Any] | None = None, max_results: int = 5, max_snippet_length: int = 100
        ) -> list[Data]:
            params = params or {}
            # 调用 SearchApi 获取完整搜索结果
            full_results = wrapper.results(query=query, **params)
            # 提取有机搜索结果（非广告），并限制数量
            organic_results = full_results.get("organic_results", [])[:max_results]

            # 将每个搜索结果转换为 Data 对象，包含标题、链接和摘要
            return [
                Data(
                    text=result.get("snippet", ""),
                    data={
                        "title": result.get("title", "")[:max_snippet_length],
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", "")[:max_snippet_length],
                    },
                )
                for result in organic_results
            ]

        results = search_func(
            self.input_value,
            self.search_params or {},
            self.max_results,
            self.max_snippet_length,
        )
        self.status = results
        return results

    # 将搜索结果转换为 DataFrame 格式，供组件输出使用
    def fetch_content_dataframe(self) -> DataFrame:
        """Convert the search results to a DataFrame.

        Returns:
            DataFrame: A DataFrame containing the search results.
        """
        data = self.fetch_content()
        return DataFrame(data)
