# JSON 序列化和反序列化模块
import json

# 类型注解模块，用于声明变量的类型
from typing import Any

# HTTP 请求库，用于调用 Notion API
import requests

# LangChain 工具类，用于将函数包装为可被 LLM 调用的工具
from langchain_core.tools import StructuredTool

# Pydantic 数据模型，用于定义输入参数的校验规则
from pydantic import BaseModel, Field

# LangChain 工具组件基类，提供组件的基本框架
from lfx.base.langchain_utilities.model import LCToolComponent

# Langflow 工具类型定义
from lfx.field_typing import Tool

# Langflow 输入组件：多行输入、密码输入、字符串输入
from lfx.inputs.inputs import MultilineInput, SecretStrInput, StrInput

# Langflow 数据模型，用于封装组件的输出结果
from lfx.schema.data import Data


# Notion 页面创建组件，用于在 Notion 数据库中创建新页面
class NotionPageCreator(LCToolComponent):
    # 组件显示名称
    display_name: str = "Create Page "
    # 组件描述信息
    description: str = "A component for creating Notion pages."
    # 组件文档链接
    documentation: str = "https://docs.langflow.org/bundles-notion"
    # 组件图标
    icon = "NotionDirectoryLoader"

    # 组件输入参数列表
    inputs = [
        # Notion 数据库 ID 输入框
        StrInput(
            name="database_id",
            display_name="Database ID",
            info="The ID of the Notion database.",
        ),
        # Notion 集成令牌密钥输入框（必填）
        SecretStrInput(
            name="notion_secret",
            display_name="Notion Secret",
            info="The Notion integration token.",
            required=True,
        ),
        # 页面属性 JSON 字符串多行输入框
        MultilineInput(
            name="properties_json",
            display_name="Properties (JSON)",
            info="The properties of the new page as a JSON string.",
        ),
    ]

    # Notion 页面创建的输入参数验证模型
    class NotionPageCreatorSchema(BaseModel):
        # Notion 数据库 ID
        database_id: str = Field(..., description="The ID of the Notion database.")
        # 页面属性 JSON 字符串
        properties_json: str = Field(..., description="The properties of the new page as a JSON string.")

    # 执行模型运行，调用 Notion API 创建页面并返回结果
    def run_model(self) -> Data:
        # 调用内部方法创建 Notion 页面
        result = self._create_notion_page(self.database_id, self.properties_json)
        # 如果返回的是字符串，说明发生了错误，将其作为文本返回
        if isinstance(result, str):
            # An error occurred, return it as text
            return Data(text=result)
        # Success, return the created page data
        # 创建成功，格式化输出页面属性信息
        output = "Created page properties:\n"
        # 遍历并拼接所有页面属性
        for prop_name, prop_value in result.get("properties", {}).items():
            output += f"{prop_name}: {prop_value}\n"
        # 返回包含文本和原始数据的 Data 对象
        return Data(text=output, data=result)

    # 构建 LangChain 结构化工具，供 LLM 调用
    def build_tool(self) -> Tool:
        return StructuredTool.from_function(
            # 工具名称
            name="create_notion_page",
            # 工具描述，提示 LLM 在使用前先检查数据库属性
            description="Create a new page in a Notion database. "
            "IMPORTANT: Use the tool to check the Database properties for more details before using this tool.",
            # 绑定的执行函数
            func=self._create_notion_page,
            # 输入参数校验模型
            args_schema=self.NotionPageCreatorSchema,
        )

    # 内部方法：通过 Notion API 在指定数据库中创建新页面
    def _create_notion_page(self, database_id: str, properties_json: str) -> dict[str, Any] | str:
        # 校验输入参数是否为空
        if not database_id or not properties_json:
            return "Invalid input. Please provide 'database_id' and 'properties_json'."

        try:
            # 将 JSON 字符串解析为 Python 字典
            properties = json.loads(properties_json)
        except json.JSONDecodeError as e:
            # JSON 格式错误时返回错误信息
            return f"Invalid properties format. Please provide a valid JSON string. Error: {e}"

        # 构造请求头，包含授权令牌和 Notion API 版本
        headers = {
            "Authorization": f"Bearer {self.notion_secret}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        # 构造请求体，包含父数据库 ID 和页面属性
        data = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }

        try:
            # 向 Notion API 发送 POST 请求创建页面
            response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data, timeout=10)
            # 检查响应状态码，非 2xx 时抛出异常
            response.raise_for_status()
            # 返回创建成功的页面 JSON 数据
            return response.json()
        except requests.exceptions.RequestException as e:
            # 捕获请求异常并构造错误信息
            error_message = f"Failed to create Notion page. Error: {e}"
            # 如果异常包含响应信息，追加状态码和响应体
            if hasattr(e, "response") and e.response is not None:
                error_message += f" Status code: {e.response.status_code}, Response: {e.response.text}"
            return error_message

    # 支持通过 () 直接调用，转发到内部创建方法
    def __call__(self, *args, **kwargs):
        return self._create_notion_page(*args, **kwargs)
