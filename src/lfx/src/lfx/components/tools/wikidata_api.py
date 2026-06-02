# 类型注解，用于声明变量类型
from typing import Any

# HTTP 客户端库，用于发送 HTTP 请求
import httpx

# LangChain 工具相关类：结构化工具和工具异常
from langchain_core.tools import StructuredTool, ToolException

# Pydantic 数据模型和字段定义
from pydantic import BaseModel, Field

# LangChain 工具组件基类
from lfx.base.langchain_utilities.model import LCToolComponent

# 工具类型注解
from lfx.field_typing import Tool

# 多行输入组件
from lfx.inputs.inputs import MultilineInput

# 数据模型，用于封装 API 返回结果
from lfx.schema.data import Data


class WikidataSearchSchema(BaseModel):
    """Wikidata 搜索参数的数据模型（Pydantic Schema），定义了工具的输入参数结构。"""

    # 搜索查询字符串，必填字段
    query: str = Field(..., description="The search query for Wikidata")


class WikidataAPIWrapper(BaseModel):
    """Wikidata API 的封装类，提供对 Wikidata 搜索接口的便捷调用。"""

    # Wikidata API 的默认端点地址
    wikidata_api_url: str = "https://www.wikidata.org/w/api.php"

    def results(self, query: str) -> list[dict[str, Any]]:
        """执行 Wikidata 搜索并返回结果列表。"""
        # 定义 Wikidata API 的请求参数
        params = {
            "action": "wbsearchentities",
            "format": "json",
            "search": query,
            "language": "en",
        }

        # 向 Wikidata API 发送 GET 请求
        response = httpx.get(self.wikidata_api_url, params=params)
        response.raise_for_status()
        response_json = response.json()

        # 提取并返回搜索结果
        return response_json.get("search", [])

    def run(self, query: str) -> list[dict[str, Any]]:
        """执行搜索并在无结果时抛出异常。"""
        try:
            results = self.results(query)
            if results:
                return results

            error_message = "No search results found for the given query."

            raise ToolException(error_message)

        except Exception as e:
            error_message = f"Error in Wikidata Search API: {e!s}"

            raise ToolException(error_message) from e


class WikidataAPIComponent(LCToolComponent):
    """Wikidata API 工具组件，通过 Wikidata 搜索接口执行相似性搜索并返回结构化数据。"""

    display_name = "Wikidata API"
    description = "Performs a search using the Wikidata API."
    name = "WikidataAPI"
    icon = "Wikipedia"
    # 标记为遗留组件，已被 wikipedia.WikidataComponent 替代
    legacy = True
    # 推荐的替代组件
    replacement = ["wikipedia.WikidataComponent"]

    inputs = [
        MultilineInput(
            name="query",
            display_name="Query",
            info="The text query for similarity search on Wikidata.",
            required=True,
        ),
    ]

    def build_tool(self) -> Tool:
        """构建并返回 LangChain 结构化工具实例。"""
        wrapper = WikidataAPIWrapper()

        # 使用 StructuredTool 和 wrapper 的 run 方法定义工具
        tool = StructuredTool.from_function(
            name="wikidata_search_api",
            description="Perform similarity search on Wikidata API",
            func=wrapper.run,
            args_schema=WikidataSearchSchema,
        )

        self.status = "Wikidata Search API Tool for Langchain"

        return tool

    def run_model(self) -> list[Data]:
        """执行搜索并将结果转换为 Data 对象列表。"""
        tool = self.build_tool()

        results = tool.run({"query": self.query})

        # 将 API 响应转换为 Data 对象列表
        data = [
            Data(
                text=result["label"],
                metadata=result,
            )
            for result in results
        ]

        self.status = data  # type: ignore[assignment]

        return data
