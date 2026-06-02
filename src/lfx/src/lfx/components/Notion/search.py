from typing import Any

import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import DropdownInput, SecretStrInput, StrInput
from lfx.schema.data import Data


# Notion 搜索组件
# 用于在 Notion 中搜索所有已与集成共享的页面和数据库
class NotionSearch(LCToolComponent):
    # 组件显示名称
    display_name: str = "Search "
    # 组件描述
    description: str = "Searches all pages and databases that have been shared with an integration."
    # 组件文档链接
    documentation: str = "https://docs.langflow.org/bundles-notion"
    # 组件图标
    icon = "NotionDirectoryLoader"

    # 组件输入定义
    inputs = [
        # Notion 集成密钥（必填，用于 API 认证）
        SecretStrInput(
            name="notion_secret",
            display_name="Notion Secret",
            info="The Notion integration token.",
            required=True,
        ),
        # 搜索查询文本，用于与页面和数据库标题进行匹配
        StrInput(
            name="query",
            display_name="Search Query",
            info="The text that the API compares page and database titles against.",
        ),
        # 结果类型过滤：仅页面或仅数据库
        DropdownInput(
            name="filter_value",
            display_name="Filter Type",
            info="Limits the results to either only pages or only databases.",
            options=["page", "database"],
            value="page",
        ),
        # 排序方向：升序或降序
        DropdownInput(
            name="sort_direction",
            display_name="Sort Direction",
            info="The direction to sort the results.",
            options=["ascending", "descending"],
            value="descending",
        ),
    ]

    # Notion 搜索参数的 Pydantic 校验模型
    # 用于构建 StructuredTool 的参数 schema
    class NotionSearchSchema(BaseModel):
        # 搜索查询文本
        query: str = Field(..., description="The search query text.")
        # 过滤类型："page" 或 "database"
        filter_value: str = Field(default="page", description="Filter type: 'page' or 'database'.")
        # 排序方向："ascending" 或 "descending"
        sort_direction: str = Field(default="descending", description="Sort direction: 'ascending' or 'descending'.")

    def run_model(self) -> list[Data]:
        """执行 Notion 搜索并返回结构化的搜索结果。

        调用 Notion API 搜索页面和数据库，将原始 JSON 响应
        转换为 Data 对象列表，每个对象包含文本摘要和元数据字典。
        同时将结果保存到 self.status 供后续组件使用。
        """
        # 调用 Notion API 执行搜索
        results = self._search_notion(self.query, self.filter_value, self.sort_direction)
        # 存储转换后的 Data 对象列表
        records = []
        # 用于拼接所有搜索结果的文本摘要
        combined_text = f"Results found: {len(results)}\n\n"

        for result in results:
            # 构建每条结果的元数据字典
            result_data = {
                "id": result["id"],
                "type": result["object"],
                "last_edited_time": result["last_edited_time"],
            }

            if result["object"] == "page":
                # 页面类型：使用 URL 作为标题或链接
                result_data["title_or_url"] = result["url"]
                text = f"id: {result['id']}\ntitle_or_url: {result['url']}\n"
            elif result["object"] == "database":
                # 数据库类型：提取数据库标题（若有）
                if "title" in result and isinstance(result["title"], list) and len(result["title"]) > 0:
                    result_data["title_or_url"] = result["title"][0]["plain_text"]
                    text = f"id: {result['id']}\ntitle_or_url: {result['title'][0]['plain_text']}\n"
                else:
                    # 数据库无标题时使用 "N/A"
                    result_data["title_or_url"] = "N/A"
                    text = f"id: {result['id']}\ntitle_or_url: N/A\n"

            # 追加对象类型和最后编辑时间
            text += f"type: {result['object']}\nlast_edited_time: {result['last_edited_time']}\n\n"
            combined_text += text
            # 将文本和元数据封装为 Data 对象
            records.append(Data(text=text, data=result_data))

        # 保存状态供下游组件访问
        self.status = records
        return records

    def build_tool(self) -> Tool:
        """构建 LangChain StructuredTool。

        将 _search_notion 方法包装为可被 LLM Agent 调用的工具，
        使用 NotionSearchSchema 作为参数校验模型。
        """
        return StructuredTool.from_function(
            name="notion_search",
            # 工具描述：说明功能和预期输入
            description="Search Notion pages and databases. "
            "Input should include the search query and optionally filter type and sort direction.",
            func=self._search_notion,
            args_schema=self.NotionSearchSchema,
        )

    def _search_notion(
        self, query: str, filter_value: str = "page", sort_direction: str = "descending"
    ) -> list[dict[str, Any]]:
        """调用 Notion Search API 执行搜索。

        通过 POST 请求向 Notion API 发送搜索条件，返回匹配的页面和数据库列表。
        使用 Notion API 版本 2022-06-28，按最后编辑时间排序。

        Args:
            query: 搜索关键词，与页面/数据库标题匹配
            filter_value: 结果过滤类型，"page" 或 "database"
            sort_direction: 排序方向，"ascending" 或 "descending"

        Returns:
            搜索结果列表，每个元素为 Notion API 返回的原始 JSON 字典
        """
        # Notion Search API 端点
        url = "https://api.notion.com/v1/search"
        # 请求头：包含认证令牌、内容类型和 API 版本
        headers = {
            "Authorization": f"Bearer {self.notion_secret}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        # 构建请求体：查询条件、过滤器和排序规则
        data = {
            "query": query,
            # 按对象类型过滤（page 或 database）
            "filter": {"value": filter_value, "property": "object"},
            # 按最后编辑时间排序
            "sort": {"direction": sort_direction, "timestamp": "last_edited_time"},
        }

        # 发送 POST 请求，超时时间 10 秒
        response = requests.post(url, headers=headers, json=data, timeout=10)
        # 如果响应状态码不是 2xx，抛出异常
        response.raise_for_status()

        # 解析 JSON 响应并返回搜索结果列表
        results = response.json()
        return results["results"]
