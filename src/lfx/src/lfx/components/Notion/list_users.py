# 该文件实现了 Notion 用户列表组件，用于从 Notion API 获取并格式化用户信息
import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import SecretStrInput
from lfx.schema.data import Data


class NotionUserList(LCToolComponent):
    """从 Notion 获取用户列表的 Langflow 组件"""

    # 组件在画布上显示的名称
    display_name = "List Users "
    # 组件描述
    description = "Retrieve users from Notion."
    # 组件文档链接
    documentation = "https://docs.langflow.org/bundles-notion"
    # 组件图标
    icon = "NotionDirectoryLoader"

    # 组件输入参数列表
    inputs = [
        SecretStrInput(
            name="notion_secret",
            display_name="Notion Secret",
            info="The Notion integration token.",
            required=True,
        ),
    ]

    # Notion 用户列表的输入参数 schema（当前无额外参数）
    class NotionUserListSchema(BaseModel):
        pass

    def run_model(self) -> list[Data]:
        """执行模型：获取 Notion 用户列表并格式化为 Data 对象返回"""
        users = self._list_users()
        records = []
        combined_text = ""

        for user in users:
            # 将每个用户的字段格式化为可读文本，下划线替换为空格并首字母大写
            output = "User:\n"
            for key, value in user.items():
                output += f"{key.replace('_', ' ').title()}: {value}\n"
            output += "________________________\n"

            combined_text += output
            records.append(Data(text=output, data=user))

        # 将结果存入 status 供 UI 展示
        self.status = records
        return records

    def build_tool(self) -> Tool:
        """构建 LangChain StructuredTool，供 AI Agent 调用"""
        return StructuredTool.from_function(
            name="notion_list_users",
            description="Retrieve users from Notion.",
            func=self._list_users,
            args_schema=self.NotionUserListSchema,
        )

    def _list_users(self) -> list[dict]:
        """通过 Notion API 获取所有用户，并提取关键字段返回"""
        # Notion 用户列表接口地址
        url = "https://api.notion.com/v1/users"
        # 请求头：包含授权令牌和 Notion API 版本号
        headers = {
            "Authorization": f"Bearer {self.notion_secret}",
            "Notion-Version": "2022-06-28",
        }

        response = requests.get(url, headers=headers, timeout=10)
        # 若响应状态码不是 2xx，抛出 HTTPError
        response.raise_for_status()

        data = response.json()
        results = data["results"]

        users = []
        for user in results:
            # 提取每个用户的 id、类型、名称和头像地址
            user_data = {
                "id": user["id"],
                "type": user["type"],
                "name": user.get("name", ""),
                "avatar_url": user.get("avatar_url", ""),
            }
            users.append(user_data)

        return users
