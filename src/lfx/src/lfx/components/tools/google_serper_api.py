from typing import Any

from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import (
    DictInput,
    DropdownInput,
    IntInput,
    MultilineInput,
    SecretStrInput,
)
from lfx.schema.data import Data


# 查询参数的数据校验模型，用于 StructuredTool 的参数定义
class QuerySchema(BaseModel):
    # 查询内容，必填
    query: str = Field(..., description="The query to search for.")
    # 搜索类型，可选 "search"（网页搜索）或 "news"（新闻搜索）
    query_type: str = Field(
        "search",
        description="The type of search to perform (e.g., 'news' or 'search').",
    )
    # 返回结果数量
    k: int = Field(4, description="The number of results to return.")
    # 额外的查询参数，如地区 (gl)、语言 (hl) 等
    query_params: dict[str, Any] = Field({}, description="Additional query parameters to pass to the API.")


# Google Serper API 组件，通过 Serper.dev 提供 Google 搜索能力
# 该组件已标记为 legacy（弃用），不再建议新用户使用
class GoogleSerperAPIComponent(LCToolComponent):
    # 组件在画布上的显示名称，包含 [DEPRECATED] 标记
    display_name = "Google Serper API [DEPRECATED]"
    # 组件描述
    description = "Call the Serper.dev Google Search API."
    # 组件内部唯一标识名
    name = "GoogleSerperAPI"
    # 画布上的图标
    icon = "Google"
    # 标记为遗留组件，已有流程中的该组件仍可运行，但不可新增
    legacy = True
    # 组件输入参数定义列表
    inputs = [
        SecretStrInput(name="serper_api_key", display_name="Serper API Key", required=True),
        MultilineInput(
            name="query",
            display_name="Query",
        ),
        IntInput(name="k", display_name="Number of results", value=4, required=True),
        DropdownInput(
            name="query_type",
            display_name="Query Type",
            required=False,
            options=["news", "search"],
            value="search",
        ),
        DictInput(
            name="query_params",
            display_name="Query Params",
            required=False,
            value={
                "gl": "us",
                "hl": "en",
            },
            list=True,
        ),
    ]

    # 执行 Google 搜索并返回结果列表
    # 根据 query_type（search/news）从不同的结果字段中提取数据
    def run_model(self) -> Data | list[Data]:
        wrapper = self._build_wrapper(self.k, self.query_type, self.query_params)
        results = wrapper.results(query=self.query)

        # Adjust the extraction based on the `type`
        if self.query_type == "search":
            list_results = results.get("organic", [])
        elif self.query_type == "news":
            list_results = results.get("news", [])
        else:
            list_results = []

        data_list = []
        for result in list_results:
            result["text"] = result.pop("snippet", "")
            data_list.append(Data(data=result))
        self.status = data_list
        return data_list

    # 构建 LangChain StructuredTool 实例，使组件可作为 Agent 工具使用
    def build_tool(self) -> Tool:
        return StructuredTool.from_function(
            name="google_search",
            description="Search Google for recent results.",
            func=self._search,
            args_schema=self.QuerySchema,
        )

    # 内部方法：根据参数构建 GoogleSerperAPIWrapper 实例
    # 将 API 密钥、结果数量、搜索类型和额外参数合并后传给包装器
    def _build_wrapper(
        self,
        k: int = 5,
        query_type: str = "search",
        query_params: dict | None = None,
    ) -> GoogleSerperAPIWrapper:
        wrapper_args = {
            "serper_api_key": self.serper_api_key,
            "k": k,
            "type": query_type,
        }

        # Add query_params if provided
        if query_params:
            wrapper_args.update(query_params)  # Merge with additional query params

        # Dynamically pass parameters to the wrapper
        return GoogleSerperAPIWrapper(**wrapper_args)

    # 内部搜索方法，供 StructuredTool 回调使用
    def _search(
        self,
        query: str,
        k: int = 5,
        query_type: str = "search",
        query_params: dict | None = None,
    ) -> dict:
        wrapper = self._build_wrapper(k, query_type, query_params)
        return wrapper.results(query=query)
