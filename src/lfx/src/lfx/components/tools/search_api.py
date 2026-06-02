# Search API 组件模块
# 提供基于 searchapi.io 的搜索引擎功能组件

from typing import Any

from langchain_community.utilities.searchapi import SearchApiAPIWrapper
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import DictInput, IntInput, MessageTextInput, MultilineInput, SecretStrInput
from lfx.schema.data import Data


class SearchAPIComponent(LCToolComponent):
    # Search API 组件类
    # 封装 searchapi.io API，支持结果数量限制和片段长度控制的搜索引擎组件
    display_name: str = "Search API"
    description: str = "Call the searchapi.io API with result limiting"
    name = "SearchAPI"
    documentation: str = "https://www.searchapi.io/docs/google"
    icon = "SearchAPI"
    legacy = True
    # 该组件已标记为遗留版本，推荐使用新的 searchapi.SearchComponent
    replacement = ["searchapi.SearchComponent"]

    # 组件输入参数定义
    inputs = [
        # 搜索引擎类型，默认为 Google
        MessageTextInput(name="engine", display_name="Engine", value="google"),
        # SearchAPI 密钥，必填项
        SecretStrInput(name="api_key", display_name="SearchAPI API Key", required=True),
        # 搜索查询输入，支持多行文本
        MultilineInput(
            name="input_value",
            display_name="Input",
        ),
        # 额外的搜索参数，高级选项
        DictInput(name="search_params", display_name="Search parameters", advanced=True, is_list=True),
        # 最大返回结果数量，默认为 5
        IntInput(name="max_results", display_name="Max Results", value=5, advanced=True),
        # 每个结果片段的最大长度，默认为 100 字符
        IntInput(name="max_snippet_length", display_name="Max Snippet Length", value=100, advanced=True),
    ]

    class SearchAPISchema(BaseModel):
        # Search API 工具的输入参数模型定义
        # 定义了搜索查询、额外参数、最大结果数和片段长度限制
        query: str = Field(..., description="The search query")
        params: dict[str, Any] = Field(default_factory=dict, description="Additional search parameters")
        max_results: int = Field(5, description="Maximum number of results to return")
        max_snippet_length: int = Field(100, description="Maximum length of each result snippet")

    def _build_wrapper(self):
        # 构建 SearchApiAPIWrapper 实例
        # 使用配置的搜索引擎和 API 密钥初始化包装器
        return SearchApiAPIWrapper(engine=self.engine, searchapi_api_key=self.api_key)

    def build_tool(self) -> Tool:
        # 构建并返回结构化搜索工具
        # 创建一个封装了搜索逻辑的 StructuredTool 实例
        wrapper = self._build_wrapper()

        def search_func(
            query: str, params: dict[str, Any] | None = None, max_results: int = 5, max_snippet_length: int = 100
        ) -> list[dict[str, Any]]:
            # 搜索执行函数
            # 调用 searchapi.io API 执行搜索，并对结果进行数量和长度限制
            params = params or {}
            # 获取原始搜索结果
            full_results = wrapper.results(query=query, **params)
            # 提取有机搜索结果，并限制数量
            organic_results = full_results.get("organic_results", [])[:max_results]

            # 处理并限制每个结果的片段长度
            limited_results = []
            for result in organic_results:
                limited_result = {
                    "title": result.get("title", "")[:max_snippet_length],
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")[:max_snippet_length],
                }
                limited_results.append(limited_result)

            return limited_results

        # 使用函数创建结构化工具
        tool = StructuredTool.from_function(
            name="search_api",
            description="Search for recent results using searchapi.io with result limiting",
            func=search_func,
            args_schema=self.SearchAPISchema,
        )

        # 设置组件状态，记录使用的搜索引擎
        self.status = f"Search API Tool created with engine: {self.engine}"
        return tool

    def run_model(self) -> list[Data]:
        # 执行搜索模型
        # 使用构建的工具执行搜索，并将结果转换为 Data 对象列表
        tool = self.build_tool()
        results = tool.run(
            {
                "query": self.input_value,
                "params": self.search_params or {},
                "max_results": self.max_results,
                "max_snippet_length": self.max_snippet_length,
            }
        )

        # 将搜索结果转换为 Data 对象，使用 snippet 作为文本内容
        data_list = [Data(data=result, text=result.get("snippet", "")) for result in results]

        # 设置组件状态为结果列表
        self.status = data_list
        return data_list
