import json
from typing import Any

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import StructuredTool
from markdown import markdown
from pydantic import BaseModel, Field

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import MultilineInput, SecretStrInput, StrInput
from lfx.log.logger import logger
from lfx.schema.data import Data

# Markdown 表格在 Notion 中的最小行数要求（包含表头、分隔符行和至少一行数据）
MIN_ROWS_IN_TABLE = 3


# Notion 页面内容添加组件：将 Markdown 文本转换为 Notion 块并追加到指定页面
class AddContentToPage(LCToolComponent):
    display_name: str = "Add Content to Page "
    description: str = "Convert markdown text to Notion blocks and append them to a Notion page."
    documentation: str = "https://developers.notion.com/reference/patch-block-children"
    icon = "NotionDirectoryLoader"

    inputs = [
        MultilineInput(
            name="markdown_text",
            display_name="Markdown Text",
            info="The markdown text to convert to Notion blocks.",
        ),
        StrInput(
            name="block_id",
            display_name="Page/Block ID",
            info="The ID of the page/block to add the content.",
        ),
        SecretStrInput(
            name="notion_secret",
            display_name="Notion Secret",
            info="The Notion integration token.",
            required=True,
        ),
    ]

    # 用于 StructuredTool 的参数 Schema 定义
    class AddContentToPageSchema(BaseModel):
        markdown_text: str = Field(..., description="The markdown text to convert to Notion blocks.")
        block_id: str = Field(..., description="The ID of the page/block to add the content.")

    # 组件直接执行时的入口方法：将 Markdown 内容添加到 Notion 页面并返回结果数据
    def run_model(self) -> Data:
        result = self._add_content_to_page(self.markdown_text, self.block_id)
        return Data(data=result, text=json.dumps(result))

    # 构建 LangChain StructuredTool，供 Agent 或其他工具调用方使用
    def build_tool(self) -> Tool:
        return StructuredTool.from_function(
            name="add_content_to_notion_page",
            description="Convert markdown text to Notion blocks and append them to a Notion page.",
            func=self._add_content_to_page,
            args_schema=self.AddContentToPageSchema,
        )

    # 核心方法：将 Markdown 文本转换为 Notion 块并通过 API 追加到指定页面
    def _add_content_to_page(self, markdown_text: str, block_id: str) -> dict[str, Any] | str:
        try:
            # 将 Markdown 转为 HTML，再由 BeautifulSoup 解析为 DOM 树
            html_text = markdown(markdown_text)
            soup = BeautifulSoup(html_text, "html.parser")
            # 递归遍历 DOM 节点，转换为 Notion 块列表
            blocks = self.process_node(soup)

            # 调用 Notion API 追加子块到目标页面/块
            url = f"https://api.notion.com/v1/blocks/{block_id}/children"
            headers = {
                "Authorization": f"Bearer {self.notion_secret}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            data = {
                "children": blocks,
            }

            response = requests.patch(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()

            return response.json()
        except requests.exceptions.RequestException as e:
            # 处理 HTTP 请求异常，包含状态码和响应体信息
            error_message = f"Error: Failed to add content to Notion page. {e}"
            if hasattr(e, "response") and e.response is not None:
                error_message += f" Status code: {e.response.status_code}, Response: {e.response.text}"
            return error_message
        except Exception as e:  # noqa: BLE001
            logger.debug("Error adding content to Notion page", exc_info=True)
            return f"Error: An unexpected error occurred while adding content to Notion page. {e}"

    # 递归遍历 HTML 节点树，将每个节点转换为对应的 Notion 块
    def process_node(self, node):
        blocks = []
        if isinstance(node, str):
            # 处理纯文本节点，识别 Markdown 格式的标题（# 开头）
            text = node.strip()
            if text:
                if text.startswith("#"):
                    heading_level = text.count("#", 0, 6)
                    heading_text = text[heading_level:].strip()
                    if heading_level in range(3):
                        blocks.append(self.create_block(f"heading_{heading_level + 1}", heading_text))
                else:
                    blocks.append(self.create_block("paragraph", text))
        elif node.name == "h1":
            blocks.append(self.create_block("heading_1", node.get_text(strip=True)))
        elif node.name == "h2":
            blocks.append(self.create_block("heading_2", node.get_text(strip=True)))
        elif node.name == "h3":
            blocks.append(self.create_block("heading_3", node.get_text(strip=True)))
        elif node.name == "p":
            # 段落节点：优先检测是否包含代码块，其次检测是否为表格，否则作为普通段落
            code_node = node.find("code")
            if code_node:
                code_text = code_node.get_text()
                language, code = self.extract_language_and_code(code_text)
                blocks.append(self.create_block("code", code, language=language))
            elif self.is_table(str(node)):
                blocks.extend(self.process_table(node))
            else:
                blocks.append(self.create_block("paragraph", node.get_text(strip=True)))
        elif node.name == "ul":
            # 无序列表，转换为 Notion 的 bulleted_list_item
            blocks.extend(self.process_list(node, "bulleted_list_item"))
        elif node.name == "ol":
            # 有序列表，转换为 Notion 的 numbered_list_item
            blocks.extend(self.process_list(node, "numbered_list_item"))
        elif node.name == "blockquote":
            blocks.append(self.create_block("quote", node.get_text(strip=True)))
        elif node.name == "hr":
            blocks.append(self.create_block("divider", ""))
        elif node.name == "img":
            blocks.append(self.create_block("image", "", image_url=node.get("src")))
        elif node.name == "a":
            blocks.append(self.create_block("bookmark", node.get_text(strip=True), link_url=node.get("href")))
        elif node.name == "table":
            blocks.extend(self.process_table(node))

        # 递归处理所有子节点
        for child in node.children:
            if isinstance(child, str):
                continue
            blocks.extend(self.process_node(child))

        return blocks

    # 从代码块文本中提取语言标识和代码内容（按首行分隔）
    def extract_language_and_code(self, code_text):
        lines = code_text.split("\n")
        language = lines[0].strip()
        code = "\n".join(lines[1:]).strip()
        return language, code

    # 判断文本是否为代码块（以 ``` 开头）
    def is_code_block(self, text):
        return text.startswith("```")

    # 从代码块文本中提取语言和代码（处理反引号包裹的情况）
    def extract_code_block(self, text):
        lines = text.split("\n")
        language = lines[0].strip("`").strip()
        code = "\n".join(lines[1:]).strip("`").strip()
        return language, code

    # 判断文本内容是否为 Markdown 表格格式（至少需要表头、分隔符行和一行数据）
    def is_table(self, text):
        rows = text.split("\n")
        if len(rows) < MIN_ROWS_IN_TABLE:
            return False

        has_separator = False
        for i, row in enumerate(rows):
            if "|" in row:
                cells = [cell.strip() for cell in row.split("|")]
                cells = [cell for cell in cells if cell]  # 移除空单元格
                # 检查第二行是否为分隔符行（由 - 和 | 组成）
                if i == 1 and all(set(cell) <= set("-|") for cell in cells):
                    has_separator = True
                elif not cells:
                    return False

        return has_separator

    # 处理列表节点，将 HTML 列表项转换为 Notion 列表块
    # 支持检测复选框语法 [x] 和 [ ]，转换为 to_do 类型块
    def process_list(self, node, list_type):
        blocks = []
        for item in node.find_all("li"):
            item_text = item.get_text(strip=True)
            checked = item_text.startswith("[x]")
            is_checklist = item_text.startswith("[ ]") or checked

            if is_checklist:
                # 复选框列表项，转换为 Notion 的 to_do 块
                item_text = item_text.replace("[x]", "").replace("[ ]", "").strip()
                blocks.append(self.create_block("to_do", item_text, checked=checked))
            else:
                blocks.append(self.create_block(list_type, item_text))
        return blocks

    # 处理 HTML 表格节点，转换为 Notion 的 table + table_row 块结构
    def process_table(self, node):
        blocks = []
        header_row = node.find("thead").find("tr") if node.find("thead") else None
        body_rows = node.find("tbody").find_all("tr") if node.find("tbody") else []

        if header_row or body_rows:
            # 计算表格最大列数，用于设置 table_width
            table_width = max(
                len(header_row.find_all(["th", "td"])) if header_row else 0,
                *(len(row.find_all(["th", "td"])) for row in body_rows),
            )

            # 创建表格容器块
            table_block = self.create_block("table", "", table_width=table_width, has_column_header=bool(header_row))
            blocks.append(table_block)

            # 添加表头行
            if header_row:
                header_cells = [cell.get_text(strip=True) for cell in header_row.find_all(["th", "td"])]
                header_row_block = self.create_block("table_row", header_cells)
                blocks.append(header_row_block)

            # 逐行添加表格数据行
            for row in body_rows:
                cells = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
                row_block = self.create_block("table_row", cells)
                blocks.append(row_block)

        return blocks

    # 根据块类型和内容创建 Notion API 所需的块 JSON 结构
    def create_block(self, block_type: str, content: str, **kwargs) -> dict[str, Any]:
        block: dict[str, Any] = {
            "object": "block",
            "type": block_type,
            block_type: {},
        }

        if block_type in {
            "paragraph",
            "heading_1",
            "heading_2",
            "heading_3",
            "bulleted_list_item",
            "numbered_list_item",
            "quote",
        }:
            # 文本类块：使用 rich_text 数组承载内容
            block[block_type]["rich_text"] = [
                {
                    "type": "text",
                    "text": {
                        "content": content,
                    },
                }
            ]
        elif block_type == "to_do":
            # 待办事项块：包含文本内容和勾选状态
            block[block_type]["rich_text"] = [
                {
                    "type": "text",
                    "text": {
                        "content": content,
                    },
                }
            ]
            block[block_type]["checked"] = kwargs.get("checked", False)
        elif block_type == "code":
            # 代码块：包含文本内容和编程语言标识
            block[block_type]["rich_text"] = [
                {
                    "type": "text",
                    "text": {
                        "content": content,
                    },
                }
            ]
            block[block_type]["language"] = kwargs.get("language", "plain text")
        elif block_type == "image":
            # 图片块：使用外部图片 URL
            block[block_type] = {"type": "external", "external": {"url": kwargs.get("image_url", "")}}
        elif block_type == "divider":
            # 分隔线块：无需额外内容
            pass
        elif block_type == "bookmark":
            # 书签块：包含链接 URL
            block[block_type]["url"] = kwargs.get("link_url", "")
        elif block_type == "table":
            # 表格容器块：定义列数和是否包含列头
            block[block_type]["table_width"] = kwargs.get("table_width", 0)
            block[block_type]["has_column_header"] = kwargs.get("has_column_header", False)
            block[block_type]["has_row_header"] = kwargs.get("has_row_header", False)
        elif block_type == "table_row":
            # 表格行块：每行包含多个单元格，每个单元格为 rich_text 格式
            block[block_type]["cells"] = [[{"type": "text", "text": {"content": cell}} for cell in content]]

        return block
