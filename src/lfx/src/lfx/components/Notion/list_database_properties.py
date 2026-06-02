# HTTP 请求库，用于调用 Notion API
import requests

# LangChain 工具类，用于创建结构化工具
from langchain_core.tools import StructuredTool

# Pydantic 数据模型，用于参数验证
from pydantic import BaseModel, Field

# LCToolComponent 基类，Langflow 工具组件的基础
from lfx.base.langchain_utilities.model import LCToolComponent

# 工具类型定义
from lfx.field_typing import Tool

# 输入组件：字符串输入和密钥输入
from lfx.inputs.inputs import SecretStrInput, StrInput

# 日志记录器
from lfx.log.logger import logger

# 数据输出模型
from lfx.schema.data import Data


class NotionDatabaseProperties(LCToolComponent):
    # Notion 数据库属性列表组件
    # 用于获取 Notion 数据库的字段属性信息

    # 组件显示名称
    display_name: str = "List Database Properties "
    # 组件描述信息
    description: str = "Retrieve properties of a Notion database."
    # 组件文档链接
    documentation: str = "https://docs.langflow.org/bundles-notion"
    # 组件图标
    icon = "NotionDirectoryLoader"

    # 组件输入参数定义
    inputs = [
        StrInput(
            name="database_id",
            display_name="Database ID",
            # Notion 数据库的唯一标识符
            info="The ID of the Notion database.",
        ),
        SecretStrInput(
            name="notion_secret",
            display_name="Notion Secret",
            # Notion 集成令牌（密钥）
            info="The Notion integration token.",
            required=True,
        ),
    ]

    class NotionDatabasePropertiesSchema(BaseModel):
        # 工具参数的 Pydantic 模型
        # 定义 _fetch_database_properties 方法的输入参数结构
        database_id: str = Field(..., description="The ID of the Notion database.")

    def run_model(self) -> Data:
        # 执行模型，获取 Notion 数据库属性
        result = self._fetch_database_properties(self.database_id)
        if isinstance(result, str):
            # An error occurred, return it as text
            # 发生错误时，将错误信息作为文本返回
            return Data(text=result)
        # Success, return the properties
        # 成功时，返回属性数据
        return Data(text=str(result), data=result)

    def build_tool(self) -> Tool:
        # 构建 LangChain 工具实例
        return StructuredTool.from_function(
            name="notion_database_properties",
            # 工具描述：检索 Notion 数据库的属性，输入应包含数据库 ID
            description="Retrieve properties of a Notion database. Input should include the database ID.",
            func=self._fetch_database_properties,
            args_schema=self.NotionDatabasePropertiesSchema,
        )

    def _fetch_database_properties(self, database_id: str) -> dict | str:
        # 获取 Notion 数据库属性的内部方法
        # 通过 Notion API 查询指定数据库的所有字段属性
        url = f"https://api.notion.com/v1/databases/{database_id}"
        headers = {
            "Authorization": f"Bearer {self.notion_secret}",
            # Use the latest supported version
            # 使用最新支持的 Notion API 版本
            "Notion-Version": "2022-06-28",
        }
        try:
            # 发送 GET 请求获取数据库信息
            response = requests.get(url, headers=headers, timeout=10)
            # 如果响应状态码不是 2xx，抛出异常
            response.raise_for_status()
            # 解析 JSON 响应
            data = response.json()
            # 返回数据库的属性字典
            return data.get("properties", {})
        except requests.exceptions.RequestException as e:
            # 网络请求异常（连接错误、超时等）
            return f"Error fetching Notion database properties: {e}"
        except ValueError as e:
            # JSON 解析异常
            return f"Error parsing Notion API response: {e}"
        except Exception as e:  # noqa: BLE001
            # 未预期的其他异常
            logger.debug("Error fetching Notion database properties", exc_info=True)
            return f"An unexpected error occurred: {e}"
