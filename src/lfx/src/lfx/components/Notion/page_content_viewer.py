import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import SecretStrInput, StrInput
from lfx.log.logger import logger
from lfx.schema.data import Data


# Notion 页面内容查看器组件
# 用于通过 Notion API 获取指定页面的内容，并将其解析为纯文本返回
class NotionPageContent(LCToolComponent):
    display_name = "Page Content Viewer "
    # Retrieve the content of a Notion page as plain text.
    # 以纯文本形式获取 Notion 页面的内容
    description = "Retrieve the content of a Notion page as plain text."
    documentation = "https://docs.langflow.org/bundles-notion"
    icon = "NotionDirectoryLoader"

    # 组件输入参数定义
    inputs = [
        StrInput(
            name="page_id",
            display_name="Page ID",
            # 要检索的 Notion 页面 ID
            info="The ID of the Notion page to retrieve.",
        ),
        SecretStrInput(
            name="notion_secret",
            display_name="Notion Secret",
            # Notion 集成令牌（密钥）
            info="The Notion integration token.",
            required=True,
        ),
    ]

    # 用于构建 LangChain 结构化工具的参数 schema
    class NotionPageContentSchema(BaseModel):
        page_id: str = Field(..., description="The ID of the Notion page to retrieve.")

    # 作为 Langflow 组件运行时的主入口方法，返回包含页面内容的 Data 对象
    def run_model(self) -> Data:
        result = self._retrieve_page_content(self.page_id)
        if isinstance(result, str) and result.startswith("Error:"):
            # An error occurred, return it as text
            # 发生错误，将错误信息作为文本返回
            return Data(text=result)
        # Success, return the content
        # 成功，返回页面内容
        return Data(text=result, data={"content": result})

    # 构建 LangChain StructuredTool，使该组件可以作为 Agent 工具使用
    def build_tool(self) -> Tool:
        return StructuredTool.from_function(
            name="notion_page_content",
            # Retrieve the content of a Notion page as plain text.
            # 以纯文本形式获取 Notion 页面的内容
            description="Retrieve the content of a Notion page as plain text.",
            func=self._retrieve_page_content,
            args_schema=self.NotionPageContentSchema,
        )

    # 通过 Notion API 获取指定页面的所有子块（blocks）内容
    # 每次请求最多获取 100 个块，返回解析后的纯文本
    def _retrieve_page_content(self, page_id: str) -> str:
        blocks_url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        headers = {
            "Authorization": f"Bearer {self.notion_secret}",
            "Notion-Version": "2022-06-28",
        }
        try:
            blocks_response = requests.get(blocks_url, headers=headers, timeout=10)
            blocks_response.raise_for_status()
            blocks_data = blocks_response.json()
            return self.parse_blocks(blocks_data.get("results", []))
        except requests.exceptions.RequestException as e:
            error_message = f"Error: Failed to retrieve Notion page content. {e}"
            if hasattr(e, "response") and e.response is not None:
                error_message += f" Status code: {e.response.status_code}, Response: {e.response.text}"
            return error_message
        except Exception as e:  # noqa: BLE001
            logger.debug("Error retrieving Notion page content", exc_info=True)
            return f"Error: An unexpected error occurred while retrieving Notion page content. {e}"

    # 解析 Notion 页面的块（blocks）列表，将各种类型的块转换为纯文本
    # 支持的块类型：段落、标题（h1-h3）、引用、列表项、待办事项、代码块、图片、分割线
    def parse_blocks(self, blocks: list) -> str:
        content = ""
        for block in blocks:
            block_type = block.get("type")
            if block_type in {"paragraph", "heading_1", "heading_2", "heading_3", "quote"}:
                content += self.parse_rich_text(block[block_type].get("rich_text", [])) + "\n\n"
            elif block_type in {"bulleted_list_item", "numbered_list_item"}:
                content += self.parse_rich_text(block[block_type].get("rich_text", [])) + "\n"
            elif block_type == "to_do":
                content += self.parse_rich_text(block["to_do"].get("rich_text", [])) + "\n"
            elif block_type == "code":
                content += self.parse_rich_text(block["code"].get("rich_text", [])) + "\n\n"
            elif block_type == "image":
                content += f"[Image: {block['image'].get('external', {}).get('url', 'No URL')}]\n\n"
            elif block_type == "divider":
                content += "---\n\n"
        return content.strip()

    # 解析 Notion 富文本（rich_text）数组，将所有片段的纯文本拼接为一个字符串
    def parse_rich_text(self, rich_text: list) -> str:
        return "".join(segment.get("plain_text", "") for segment in rich_text)

    # 允许将组件实例作为函数直接调用，委托给 _retrieve_page_content 方法
    def __call__(self, *args, **kwargs):
        return self._retrieve_page_content(*args, **kwargs)
