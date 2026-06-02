import json
import re
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from lfx.custom.custom_component.component import Component
from lfx.io import FileInput, MultilineInput, Output
from lfx.schema.data import Data


# Google OAuth Token 组件：用于生成 Google OAuth 令牌的 JSON 字符串
# 该组件通过 Google OAuth 2.0 授权流程获取用户凭证，并将令牌信息返回
class GoogleOAuthToken(Component):
    display_name = "Google OAuth Token"
    # 组件描述：生成包含 Google OAuth 令牌的 JSON 字符串
    description = "Generates a JSON string with your Google OAuth token."
    # Google OAuth 2.0 Web 服务器应用的官方文档链接
    documentation: str = "https://developers.google.com/identity/protocols/oauth2/web-server?hl=pt-br#python_1"
    icon = "Google"
    name = "GoogleOAuthToken"
    # 标记为遗留组件，不再维护新功能
    legacy: bool = True
    # 组件输入参数定义
    inputs = [
        # Scopes 输入：允许用户以多行格式输入 OAuth 作用域（scopes），用于指定应用请求的权限范围
        MultilineInput(
            name="scopes",
            display_name="Scopes",
            info="Input scopes for your application.",
            required=True,
        ),
        # OAuth 凭证文件输入：上传 Google OAuth 客户端凭证 JSON 文件（如 credentials.json）
        FileInput(
            name="oauth_credentials",
            display_name="Credentials File",
            info="Input OAuth Credentials file (e.g. credentials.json).",
            file_types=["json"],
            required=True,
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(display_name="Output", name="output", method="build_output"),
    ]

    # 验证用户输入的 OAuth scopes 格式是否合法
    def validate_scopes(self, scopes):
        # 使用正则表达式匹配合法的 Google OAuth scopes 格式
        pattern = (
            r"^(https://www\.googleapis\.com/auth/[\w\.\-]+"
            r"|mail\.google\.com/"
            r"|www\.google\.com/calendar/feeds"
            r"|www\.google\.com/m8/feeds)"
            r"(,\s*https://www\.googleapis\.com/auth/[\w\.\-]+"
            r"|mail\.google\.com/"
            r"|www\.google\.com/calendar/feeds"
            r"|www\.google\.com/m8/feeds)*$"
        )
        if not re.match(pattern, scopes):
            error_message = "Invalid scope format."
            raise ValueError(error_message)

    # 构建输出：执行 OAuth 授权流程并返回令牌数据
    def build_output(self) -> Data:
        # 首先验证输入的 scopes 格式是否正确
        self.validate_scopes(self.scopes)

        # 将逗号分隔的 scopes 字符串解析为列表，并去除每个 scope 前后的空白字符
        user_scopes = [scope.strip() for scope in self.scopes.split(",")]
        if self.scopes:
            scopes = user_scopes
        else:
            error_message = "Incorrect scope, check the scopes field."
            raise ValueError(error_message)

        # 尝试从本地缓存的 token.json 文件加载已有的凭证
        creds = None
        token_path = Path("token.json")

        if token_path.exists():
            # 如果 token.json 存在，从中加载用户凭证
            creds = Credentials.from_authorized_user_file(str(token_path), scopes)

        # 检查凭证是否有效；如果无效则尝试刷新或重新授权
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # 凭证已过期但有刷新令牌，通过刷新获取新的访问令牌
                creds.refresh(Request())
            else:
                # 既无有效凭证也无刷新令牌，需要重新走 OAuth 授权流程
                if self.oauth_credentials:
                    client_secret_file = self.oauth_credentials
                else:
                    error_message = "OAuth 2.0 Credentials file not provided."
                    raise ValueError(error_message)

                # 使用客户端凭证文件创建 OAuth 授权流程，并在本地启动临时服务器完成授权
                flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
                creds = flow.run_local_server(port=0)

                # 将新获取的凭证缓存到本地 token.json 文件，供下次使用
                token_path.write_text(creds.to_json(), encoding="utf-8")

        # 将凭证对象序列化为 JSON 字典并返回为 Langflow 的 Data 对象
        creds_json = json.loads(creds.to_json())

        return Data(data=creds_json)
