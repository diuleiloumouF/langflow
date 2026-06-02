# Glean 搜索 API 组件
# 该文件实现了 Glean 搜索 API 的 Langflow 组件，用于通过 Glean API 进行企业搜索

import json
from typing import Any
from urllib.parse import urljoin

import httpx
from langchain_core.tools import StructuredTool, ToolException
from pydantic import BaseModel
from pydantic.v1 import Field

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import IntInput, MultilineInput, NestedDictInput, SecretStrInput, StrInput
from lfx.io import Output
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame


class GleanSearchAPISchema(BaseModel):
    """Glean 搜索 API 的参数模型，定义搜索请求的输入参数"""

    query: str = Field(..., description="The search query")
    # 搜索查询文本

    page_size: int = Field(10, description="Maximum number of results to return")
    # 每页返回的最大结果数量，默认为 10

    request_options: dict[str, Any] | None = Field(default_factory=dict, description="Request Options")
    # 请求选项，可选的附加参数


class GleanAPIWrapper(BaseModel):
    """Wrapper around Glean API."""

    # Glean API 的封装类，负责构建请求、执行搜索和处理结果

    glean_api_url: str
    # Glean API 的 URL 地址

    glean_access_token: str
    # Glean API 的访问令牌

    act_as: str = "langflow-component@datastax.com"  # TODO: Detect this
    # 模拟用户身份，用于 Glean API 的用户身份验证

    def _prepare_request(
        self,
        query: str,
        page_size: int = 10,
        request_options: dict[str, Any] | None = None,
    ) -> dict:
        """构建 Glean 搜索 API 的 HTTP 请求参数"""
        # Ensure there's a trailing slash
        # 确保 URL 末尾有斜杠
        url = self.glean_api_url
        if not url.endswith("/"):
            url += "/"

        # 返回请求的 URL、认证头和搜索载荷
        return {
            "url": urljoin(url, "search"),
            "headers": {
                "Authorization": f"Bearer {self.glean_access_token}",
                "X-Scio-ActAs": self.act_as,
            },
            "payload": {
                "query": query,
                "pageSize": page_size,
                "requestOptions": request_options,
            },
        }

    def results(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        """获取搜索结果列表，如果无结果则抛出异常"""
        results = self._search_api_results(query, **kwargs)

        if len(results) == 0:
            msg = "No good Glean Search Result was found"
            # 未找到有效的 Glean 搜索结果
            raise AssertionError(msg)

        return results

    def run(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        """执行搜索并处理结果，将标题填充到 snippets 字段"""
        try:
            results = self.results(query, **kwargs)

            processed_results = []
            for result in results:
                # 如果结果有标题但没有 snippets，将标题作为 snippet 填充
                if "title" in result:
                    result["snippets"] = result.get("snippets", [{"snippet": {"text": result["title"]}}])
                    if "text" not in result["snippets"][0]:
                        result["snippets"][0]["text"] = result["title"]

                processed_results.append(result)
        except Exception as e:
            error_message = f"Error in Glean Search API: {e!s}"
            # 捕获异常并包装为 ToolException
            raise ToolException(error_message) from e

        return processed_results

    def _search_api_results(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        """调用 Glean 搜索 API 并返回原始结果列表"""
        request_details = self._prepare_request(query, **kwargs)

        # 发送 POST 请求到 Glean 搜索 API
        response = httpx.post(
            request_details["url"],
            json=request_details["payload"],
            headers=request_details["headers"],
        )

        response.raise_for_status()
        response_json = response.json()

        # 从响应中提取 results 数组
        return response_json.get("results", [])

    @staticmethod
    def _result_as_string(result: dict) -> str:
        """将搜索结果转换为格式化的 JSON 字符串"""
        return json.dumps(result, indent=4)


class GleanSearchAPIComponent(LCToolComponent):
    """Glean 搜索 API 组件，提供通过 Glean 进行企业搜索的功能"""

    display_name: str = "Glean Search API"
    # 组件在画布上显示的名称

    description: str = "Search using Glean's API."
    # 组件描述信息

    documentation: str = "https://docs.langflow.org/bundles-glean"
    # 组件文档链接

    icon: str = "Glean"
    # 组件图标

    # 组件输出定义：以 DataFrame 格式返回搜索结果
    outputs = [
        Output(display_name="Table", name="dataframe", method="fetch_content_dataframe"),
    ]

    # 组件输入定义：API URL、访问令牌、查询文本、分页大小、请求选项
    inputs = [
        StrInput(name="glean_api_url", display_name="Glean API URL", required=True),
        SecretStrInput(name="glean_access_token", display_name="Glean Access Token", required=True),
        MultilineInput(name="query", display_name="Query", required=True, tool_mode=True),
        IntInput(name="page_size", display_name="Page Size", value=10),
        NestedDictInput(name="request_options", display_name="Request Options", required=False),
    ]

    def build_tool(self) -> Tool:
        """构建 Glean 搜索工具，用于 LangChain 集成"""
        # 创建 API 封装器实例
        wrapper = self._build_wrapper(
            glean_api_url=self.glean_api_url,
            glean_access_token=self.glean_access_token,
        )

        # 从函数创建结构化工具
        tool = StructuredTool.from_function(
            name="glean_search_api",
            description="Search Glean for relevant results.",
            func=wrapper.run,
            args_schema=GleanSearchAPISchema,
        )

        self.status = "Glean Search API Tool for Langchain"
        # 设置状态信息，表示工具已创建成功

        return tool

    def run_model(self) -> DataFrame:
        """运行模型并返回 DataFrame 格式的搜索结果"""
        return self.fetch_content_dataframe()

    def fetch_content(self) -> list[Data]:
        """执行搜索并返回 Data 对象列表"""
        # 构建工具实例
        tool = self.build_tool()

        # 使用工具执行搜索
        results = tool.run(
            {
                "query": self.query,
                "page_size": self.page_size,
                "request_options": self.request_options,
            }
        )

        # Build the data
        # 将搜索结果转换为 Data 对象列表
        data = [Data(data=result, text=result["snippets"][0]["text"]) for result in results]
        self.status = data  # type: ignore[assignment]
        # 设置状态为返回的数据

        return data

    def _build_wrapper(
        self,
        glean_api_url: str,
        glean_access_token: str,
    ):
        """创建 GleanAPIWrapper 实例"""
        return GleanAPIWrapper(
            glean_api_url=glean_api_url,
            glean_access_token=glean_access_token,
        )

    def fetch_content_dataframe(self) -> DataFrame:
        """Convert the Glean search results to a DataFrame.

        Returns:
            DataFrame: A DataFrame containing the search results.
        """
        # 将搜索结果转换为 DataFrame 格式
        data = self.fetch_content()
        return DataFrame(data)
