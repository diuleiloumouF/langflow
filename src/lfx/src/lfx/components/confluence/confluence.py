# Confluence 文档加载器组件，用于从 Atlassian Confluence Wiki 平台加载文档内容
from langchain_community.document_loaders import ConfluenceLoader
from langchain_community.document_loaders.confluence import ContentFormat

from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, DropdownInput, IntInput, Output, SecretStrInput, StrInput
from lfx.schema.data import Data


class ConfluenceComponent(Component):
    # Confluence 组件：连接 Atlassian Confluence Wiki 协作平台，加载指定空间中的文档页面
    # 支持配置站点 URL、用户凭证、空间键以及内容格式等参数
    display_name = "Confluence"
    # Confluence Wiki 协作平台
    description = "Confluence wiki collaboration platform"
    documentation = "https://python.langchain.com/v0.2/docs/integrations/document_loaders/confluence/"
    trace_type = "tool"
    icon = "Confluence"
    name = "Confluence"

    # 组件输入参数定义
    inputs = [
        StrInput(
            name="url",
            display_name="Site URL",
            required=True,
            # Confluence 站点的基础 URL，例如: https://<company>.atlassian.net/wiki
            info="The base URL of the Confluence Space. Example: https://<company>.atlassian.net/wiki.",
        ),
        StrInput(
            name="username",
            display_name="Username",
            required=True,
            # Atlassian 用户邮箱地址，例如: email@example.com
            info="Atlassian User E-mail. Example: email@example.com",
        ),
        SecretStrInput(
            name="api_key",
            display_name="Confluence API Key",
            required=True,
            # Atlassian API 密钥，可在以下地址创建: https://id.atlassian.com/manage-profile/security/api-tokens
            info="Atlassian Key. Create at: https://id.atlassian.com/manage-profile/security/api-tokens",
        ),
        # Confluence 空间键，用于指定要加载文档的空间
        StrInput(name="space_key", display_name="Space Key", required=True),
        # 是否使用 Confluence Cloud 版本（而非 Server/Data Center 版本）
        BoolInput(name="cloud", display_name="Use Cloud?", required=True, value=True, advanced=True),
        DropdownInput(
            name="content_format",
            display_name="Content Format",
            # 可选的内容格式：编辑器格式、导出视图、匿名导出视图、存储格式、视图格式
            options=[
                ContentFormat.EDITOR.value,
                ContentFormat.EXPORT_VIEW.value,
                ContentFormat.ANONYMOUS_EXPORT_VIEW.value,
                ContentFormat.STORAGE.value,
                ContentFormat.VIEW.value,
            ],
            value=ContentFormat.STORAGE.value,
            required=True,
            advanced=True,
            # 指定内容格式，默认为 Storage 格式（原始存储格式）
            info="Specify content format, defaults to ContentFormat.STORAGE",
        ),
        IntInput(
            name="max_pages",
            display_name="Max Pages",
            required=False,
            value=1000,
            advanced=True,
            # 最大检索页面数，默认为 1000
            info="Maximum number of pages to retrieve in total, defaults 1000",
        ),
    ]

    # 组件输出定义：将加载的 Confluence 文档转换为 JSON 数据
    outputs = [
        Output(name="data", display_name="JSON", method="load_documents"),
    ]

    def build_confluence(self) -> ConfluenceLoader:
        # 根据用户输入的参数构建 ConfluenceLoader 实例
        content_format = ContentFormat(self.content_format)
        return ConfluenceLoader(
            url=self.url,
            username=self.username,
            api_key=self.api_key,
            cloud=self.cloud,
            space_key=self.space_key,
            content_format=content_format,
            max_pages=self.max_pages,
        )

    def load_documents(self) -> list[Data]:
        # 加载 Confluence 文档并将 LangChain Document 对象转换为 Data 对象
        confluence = self.build_confluence()
        documents = confluence.load()
        # 使用 Data 的 from_document 方法将每个文档转换为 Data 格式
        data = [Data.from_document(doc) for doc in documents]  # Using the from_document method of Data
        # 将加载结果设置到组件状态中，便于在画布上查看
        self.status = data
        return data
