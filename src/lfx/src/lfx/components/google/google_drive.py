# Google Drive 文档加载组件，用于通过服务账号凭证从 Google Drive 加载文档
import json
from json.decoder import JSONDecodeError

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from langchain_google_community import GoogleDriveLoader

from lfx.custom.custom_component.component import Component
from lfx.helpers.data import docs_to_data
from lfx.inputs.inputs import MessageTextInput
from lfx.io import SecretStrInput
from lfx.schema.data import Data
from lfx.template.field.base import Output


# Google Drive 文档加载器组件类，继承自 Component 基类
class GoogleDriveComponent(Component):
    # 组件显示名称
    display_name = "Google Drive Loader"
    # 组件描述信息
    description = "Loads documents from Google Drive using provided credentials."
    # 组件图标
    icon = "Google"
    # 标记为旧版组件，新用户不应使用此组件
    legacy: bool = True

    # 组件输入参数定义
    inputs = [
        # 服务账号 JSON 令牌输入，包含 OAuth 2.0 凭证信息
        SecretStrInput(
            name="json_string",
            display_name="JSON String of the Service Account Token",
            info="JSON string containing OAuth 2.0 access token information for service account access",
            required=True,
        ),
        # Google Drive 文档 ID 输入
        MessageTextInput(
            name="document_id", display_name="Document ID", info="Single Google Drive document ID", required=True
        ),
    ]

    # 组件输出参数定义
    outputs = [
        Output(display_name="Loaded Documents", name="docs", method="load_documents"),
    ]

    # 加载 Google Drive 文档并返回数据
    def load_documents(self) -> Data:
        # 自定义 Google Drive 加载器，支持直接传入凭证对象
        class CustomGoogleDriveLoader(GoogleDriveLoader):
            # 凭证对象，可直接传入使用
            creds: Credentials | None = None
            """Credentials object to be passed directly."""

            # 从提供的 creds 属性加载凭证，若无则抛出异常
            def _load_credentials(self):
                """Load credentials from the provided creds attribute or fallback to the original method."""
                if self.creds:
                    return self.creds
                msg = "No credentials provided."
                raise ValueError(msg)

            class Config:
                arbitrary_types_allowed = True

        # 获取 JSON 格式的令牌字符串
        json_string = self.json_string

        # 构建文档 ID 列表
        document_ids = [self.document_id]
        if len(document_ids) != 1:
            msg = "Expected a single document ID"
            raise ValueError(msg)

        # TODO: Add validation to check if the document ID is valid
        # TODO: 添加对文档 ID 有效性的校验逻辑

        # Load the token information from the JSON string
        # 从 JSON 字符串中解析令牌信息
        try:
            token_info = json.loads(json_string)
        except JSONDecodeError as e:
            msg = "Invalid JSON string"
            raise ValueError(msg) from e

        # Initialize the custom loader with the provided credentials and document IDs
        # 使用提供的凭证和文档 ID 初始化自定义加载器
        loader = CustomGoogleDriveLoader(
            creds=Credentials.from_authorized_user_info(token_info), document_ids=document_ids
        )

        # Load the documents
        # 执行文档加载操作
        try:
            docs = loader.load()
        # catch google.auth.exceptions.RefreshError
        # 捕获 Google 认证令牌刷新失败的异常
        except RefreshError as e:
            msg = "Authentication error: Unable to refresh authentication token. Please try to reauthenticate."
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"Error loading documents: {e}"
            raise ValueError(msg) from e

        # 确保只加载了单个文档
        if len(docs) != 1:
            msg = "Expected a single document to be loaded."
            raise ValueError(msg)

        # 将文档对象转换为 Data 格式
        data = docs_to_data(docs)
        # Return the loaded documents
        # 设置组件状态并返回加载的文档数据
        self.status = data
        return Data(data={"text": data})
