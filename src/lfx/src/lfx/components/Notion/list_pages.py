import json
from typing import Any

import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import MultilineInput, SecretStrInput, StrInput
from lfx.log.logger import logger
from lfx.schema.data import Data


class NotionListPages(LCToolComponent):
    """Notion 数据库页面列表查询组件，支持过滤和排序查询 Notion 数据库中的页面。"""

    display_name: str = "List Pages "
    description: str = (
        "Query a Notion database with filtering and sorting. "
        "The input should be a JSON string containing the 'filter' and 'sorts' objects. "
        "Example input:\n"
        '{"filter": {"property": "Status", "select": {"equals": "Done"}}, '
        '"sorts": [{"timestamp": "created_time", "direction": "descending"}]}'
    )
    documentation: str = "https://docs.langflow.org/bundles-notion"
    icon = "NotionDirectoryLoader"

    # 组件输入参数定义
    inputs = [
        SecretStrInput(
            name="notion_secret",
            display_name="Notion Secret",
            info="The Notion integration token.",
            required=True,
        ),
        StrInput(
            name="database_id",
            display_name="Database ID",
            info="The ID of the Notion database to query.",
        ),
        MultilineInput(
            name="query_json",
            display_name="Database query (JSON)",
            info="A JSON string containing the filters and sorts that will be used for querying the database. "
            "Leave empty for no filters or sorts.",
        ),
    ]

    # Notion 查询参数的 Pydantic 数据模型
    class NotionListPagesSchema(BaseModel):
        database_id: str = Field(..., description="The ID of the Notion database to query.")
        query_json: str | None = Field(
            default="",
            description="A JSON string containing the filters and sorts for querying the database. "
            "Leave empty for no filters or sorts.",
        )

    def run_model(self) -> list[Data]:
        """执行 Notion 数据库查询，返回页面数据列表。"""
        result = self._query_notion_database(self.database_id, self.query_json)

        if isinstance(result, str):
            # An error occurred, return it as a single record
            # 发生错误时，将错误信息作为单条记录返回
            return [Data(text=result)]

        records = []
        combined_text = f"Pages found: {len(result)}\n\n"

        for page in result:
            page_data = {
                "id": page["id"],
                "url": page["url"],
                "created_time": page["created_time"],
                "last_edited_time": page["last_edited_time"],
                "properties": page["properties"],
            }

            text = (
                f"id: {page['id']}\n"
                f"url: {page['url']}\n"
                f"created_time: {page['created_time']}\n"
                f"last_edited_time: {page['last_edited_time']}\n"
                f"properties: {json.dumps(page['properties'], indent=2)}\n\n"
            )

            combined_text += text
            records.append(Data(text=text, **page_data))

        self.status = records
        return records

    def build_tool(self) -> Tool:
        """构建 LangChain StructuredTool，供 Agent 调用 Notion 数据库查询。"""
        return StructuredTool.from_function(
            name="notion_list_pages",
            description=self.description,
            func=self._query_notion_database,
            args_schema=self.NotionListPagesSchema,
        )

    def _query_notion_database(self, database_id: str, query_json: str | None = None) -> list[dict[str, Any]] | str:
        """调用 Notion API 查询数据库，返回页面列表或错误信息字符串。"""
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {self.notion_secret}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        # 构建查询请求体
        query_payload = {}
        if query_json and query_json.strip():
            try:
                query_payload = json.loads(query_json)
            except json.JSONDecodeError as e:
                return f"Invalid JSON format for query: {e}"

        try:
            response = requests.post(url, headers=headers, json=query_payload, timeout=10)
            response.raise_for_status()
            results = response.json()
            return results["results"]
        except requests.exceptions.RequestException as e:
            return f"Error querying Notion database: {e}"
        except KeyError:
            return "Unexpected response format from Notion API"
        except Exception as e:  # noqa: BLE001
            logger.debug("Error querying Notion database", exc_info=True)
            return f"An unexpected error occurred: {e}"
