import uuid

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, IntInput, MultilineInput, Output, SecretStrInput, StrInput
from lfx.schema.data import Data


# Firecrawl 爬虫 API 组件，用于爬取指定 URL 并返回结构化结果
class FirecrawlCrawlApi(Component):
    display_name: str = "Firecrawl Crawl API"
    description: str = "Crawls a URL and returns the results."
    name = "FirecrawlCrawlApi"

    documentation: str = "https://docs.firecrawl.dev/v1/api-reference/endpoint/crawl-post"

    # 组件输入参数定义
    inputs = [
        # Firecrawl API 密钥（密码类型，不显示明文）
        SecretStrInput(
            name="api_key",
            display_name="Firecrawl API Key",
            required=True,
            password=True,
            info="The API key to use Firecrawl API.",
        ),
        # 目标 URL（多行输入，支持工具模式）
        MultilineInput(
            name="url",
            display_name="URL",
            required=True,
            info="The URL to scrape.",
            tool_mode=True,
        ),
        # 请求超时时间（毫秒）
        IntInput(
            name="timeout",
            display_name="Timeout",
            info="Timeout in milliseconds for the request.",
        ),
        # 幂等键，用于确保请求唯一性
        StrInput(
            name="idempotency_key",
            display_name="Idempotency Key",
            info="Optional idempotency key to ensure unique requests.",
        ),
        # 爬虫选项（深度、限制、外部链接等配置）
        DataInput(
            name="crawlerOptions",
            display_name="Crawler Options",
            info="The crawler options to send with the request.",
        ),
        # 抓取选项（页面内容提取相关配置）
        DataInput(
            name="scrapeOptions",
            display_name="Scrape Options",
            info="The page options to send with the request.",
        ),
    ]

    # 组件输出：JSON 格式的爬取结果
    outputs = [
        Output(display_name="JSON", name="data", method="crawl"),
    ]
    idempotency_key: str | None = None

    def crawl(self) -> Data:
        """执行爬虫操作，爬取目标 URL 并返回结构化数据。"""
        try:
            from firecrawl import FirecrawlApp
        except ImportError as e:
            # firecrawl-py 未安装时抛出明确的安装提示
            msg = "Could not import firecrawl integration package. Please install it with `pip install firecrawl-py`."
            raise ImportError(msg) from e

        # 从 DataInput 对象中提取爬虫选项字典
        params = self.crawlerOptions.__dict__["data"] if self.crawlerOptions else {}
        scrape_options_dict = self.scrapeOptions.__dict__["data"] if self.scrapeOptions else {}
        if scrape_options_dict:
            params["scrapeOptions"] = scrape_options_dict

        # Set default values for new parameters in v1
        # 设置 v1 API 的默认参数值
        params.setdefault("maxDepth", 2)
        params.setdefault("limit", 10000)
        params.setdefault("allowExternalLinks", False)
        params.setdefault("allowBackwardLinks", False)
        params.setdefault("ignoreSitemap", False)
        params.setdefault("ignoreQueryParameters", False)

        # Ensure onlyMainContent is explicitly set if not provided
        # 确保 scrapeOptions 中包含 onlyMainContent 配置，默认仅抓取页面主体内容
        if "scrapeOptions" in params:
            params["scrapeOptions"].setdefault("onlyMainContent", True)
        else:
            params["scrapeOptions"] = {"onlyMainContent": True}

        # 如果未提供幂等键，则自动生成一个 UUID
        if not self.idempotency_key:
            self.idempotency_key = str(uuid.uuid4())

        # 创建 FirecrawlApp 实例并执行爬虫
        app = FirecrawlApp(api_key=self.api_key)
        crawl_result = app.crawl_url(self.url, params=params, idempotency_key=self.idempotency_key)
        return Data(data={"results": crawl_result})
