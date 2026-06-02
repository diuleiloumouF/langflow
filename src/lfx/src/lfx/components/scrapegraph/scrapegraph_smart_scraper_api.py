from lfx.custom.custom_component.component import Component
from lfx.io import (
    MessageTextInput,
    Output,
    SecretStrInput,
)
from lfx.schema.data import Data


# ScrapeGraph 智能爬虫 API 组件
# 通过 ScrapeGraph 的 SmartScraper 接口，对指定 URL 进行智能抓取并返回结构化数据
class ScrapeGraphSmartScraperApi(Component):
    display_name: str = "ScrapeGraph Smart Scraper API"
    # 组件描述：给定一个 URL，返回该网站的结构化数据
    description: str = "Given a URL, it will return the structured data of the website."
    name = "ScrapeGraphSmartScraperApi"

    # 输出类型为 Document，可用于下游组件链接
    output_types: list[str] = ["Document"]
    # ScrapeGraph SmartScraper 官方文档地址
    documentation: str = "https://docs.scrapegraphai.com/services/smartscraper"

    # 组件输入参数定义
    inputs = [
        # ScrapeGraph API 密钥，必填项，以密码形式隐藏显示
        SecretStrInput(
            name="api_key",
            display_name="ScrapeGraph API Key",
            required=True,
            password=True,
            info="The API key to use ScrapeGraph API.",
        ),
        # 目标网页 URL，支持工具模式输入
        MessageTextInput(
            name="url",
            display_name="URL",
            tool_mode=True,
            info="The URL to scrape.",
        ),
        # 用于智能爬虫的提示词，指导爬虫提取哪些信息
        MessageTextInput(
            name="prompt",
            display_name="Prompt",
            tool_mode=True,
            info="The prompt to use for the smart scraper.",
        ),
    ]

    # 组件输出定义，输出名称为 data，对应 scrape 方法
    outputs = [
        Output(display_name="JSON", name="data", method="scrape"),
    ]

    # 执行智能爬虫，调用 ScrapeGraph API 获取网页结构化数据并返回
    def scrape(self) -> list[Data]:
        try:
            from scrapegraph_py import Client
            from scrapegraph_py.logger import sgai_logger
        except ImportError as e:
            # scrapegraph-py 未安装时抛出友好提示
            msg = "Could not import scrapegraph-py package. Please install it with `pip install scrapegraph-py`."
            raise ImportError(msg) from e

        # Set logging level
        # 设置日志级别为 INFO
        sgai_logger.set_logging(level="INFO")

        # Initialize the client with API key
        # 使用 API 密钥初始化 ScrapeGraph 客户端
        sgai_client = Client(api_key=self.api_key)

        try:
            # SmartScraper request
            # 发送 SmartScraper 请求，传入目标 URL 和用户提示词
            response = sgai_client.smartscraper(
                website_url=self.url,
                user_prompt=self.prompt,
            )

            # Close the client
            # 关闭客户端连接，释放资源
            sgai_client.close()

            # 将返回数据包装为 Data 对象返回
            return Data(data=response)
        except Exception:
            # 发生异常时确保关闭客户端连接
            sgai_client.close()
            raise
