from lfx.custom.custom_component.component import Component
from lfx.io import (
    MessageTextInput,
    Output,
    SecretStrInput,
)
from lfx.schema.data import Data


class ScrapeGraphMarkdownifyApi(Component):
    # ScrapeGraph Markdownify API 组件：给定一个 URL，返回该网页的 Markdown 格式内容
    display_name: str = "ScrapeGraph Markdownify API"
    # 功能描述：接收 URL 输入，通过 ScrapeGraph API 将网页内容转换为 Markdown 格式
    description: str = "Given a URL, it will return the markdownified content of the website."
    name = "ScrapeGraphMarkdownifyApi"

    # 输出类型为文档类型
    output_types: list[str] = ["Document"]
    # ScrapeGraph 官方文档地址
    documentation: str = "https://docs.scrapegraphai.com/services/markdownify"

    # 组件输入参数定义
    inputs = [
        SecretStrInput(
            name="api_key",
            display_name="ScrapeGraph API Key",
            required=True,
            password=True,
            # ScrapeGraph API 密钥，用于身份验证
            info="The API key to use ScrapeGraph API.",
        ),
        MessageTextInput(
            name="url",
            display_name="URL",
            tool_mode=True,
            # 需要转换为 Markdown 格式的目标网页 URL
            info="The URL to markdownify.",
        ),
    ]

    # 组件输出定义：输出名称为 data，调用 scrape 方法
    outputs = [
        Output(display_name="JSON", name="data", method="scrape"),
    ]

    def scrape(self) -> list[Data]:
        # 延迟导入 scrapegraph-py 包，避免不必要的依赖加载
        try:
            from scrapegraph_py import Client
            from scrapegraph_py.logger import sgai_logger
        except ImportError as e:
            msg = "Could not import scrapegraph-py package. Please install it with `pip install scrapegraph-py`."
            raise ImportError(msg) from e

        # Set logging level
        # 设置日志级别为 INFO
        sgai_logger.set_logging(level="INFO")

        # Initialize the client with API key
        # 使用 API 密钥初始化 ScrapeGraph 客户端
        sgai_client = Client(api_key=self.api_key)

        try:
            # Markdownify request
            # 调用 ScrapeGraph 的 markdownify 接口，将网页转换为 Markdown
            response = sgai_client.markdownify(
                website_url=self.url,
            )

            # Close the client
            # 关闭客户端连接，释放资源
            sgai_client.close()

            # 将响应数据包装为 Data 对象返回
            return Data(data=response)
        except Exception:
            # 发生异常时也要确保关闭客户端连接
            sgai_client.close()
            raise
