# 导入自定义组件基类
from lfx.custom.custom_component.component import Component

# 导入输入输出组件类型
from lfx.io import (
    BoolInput,
    MultilineInput,
    Output,
    SecretStrInput,
)

# 导入数据模型
from lfx.schema.data import Data


class FirecrawlMapApi(Component):
    """Firecrawl Map API 组件，用于映射 URL 并返回结果。"""

    display_name: str = "Firecrawl Map API"
    description: str = "Maps a URL and returns the results."
    name = "FirecrawlMapApi"

    documentation: str = "https://docs.firecrawl.dev/api-reference/endpoint/map"

    # 组件输入参数定义
    inputs = [
        # API 密钥输入
        SecretStrInput(
            name="api_key",
            display_name="Firecrawl API Key",
            required=True,
            password=True,
            info="The API key to use Firecrawl API.",
        ),
        # URL 列表输入，支持逗号或换行分隔
        MultilineInput(
            name="urls",
            display_name="URLs",
            required=True,
            info="List of URLs to create maps from (separated by commas or new lines).",
            tool_mode=True,
        ),
        # 是否忽略 sitemap.xml 文件
        BoolInput(
            name="ignore_sitemap",
            display_name="Ignore Sitemap",
            info="When true, the sitemap.xml file will be ignored during crawling.",
        ),
        # 是否仅返回 sitemap 中的链接
        BoolInput(
            name="sitemap_only",
            display_name="Sitemap Only",
            info="When true, only links found in the sitemap will be returned.",
        ),
        # 是否包含子域名
        BoolInput(
            name="include_subdomains",
            display_name="Include Subdomains",
            info="When true, subdomains of the provided URL will also be scanned.",
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(display_name="JSON", name="data", method="map"),
    ]

    def map(self) -> Data:
        """执行 URL 映射操作，返回包含所有链接的数据。"""
        try:
            from firecrawl import FirecrawlApp
        except ImportError as e:
            msg = "Could not import firecrawl integration package. Please install it with `pip install firecrawl-py`."
            raise ImportError(msg) from e

        # Validate URLs
        # 验证 URL 是否提供
        if not self.urls:
            msg = "URLs are required"
            raise ValueError(msg)

        # Split and validate URLs (handle both commas and newlines)
        # 分割并验证 URL（支持逗号和换行符分隔）
        urls = [url.strip() for url in self.urls.replace("\n", ",").split(",") if url.strip()]
        if not urls:
            msg = "No valid URLs provided"
            raise ValueError(msg)

        # 构建映射参数
        params = {
            "ignoreSitemap": self.ignore_sitemap,
            "sitemapOnly": self.sitemap_only,
            "includeSubdomains": self.include_subdomains,
        }

        # 初始化 Firecrawl 应用
        app = FirecrawlApp(api_key=self.api_key)

        # Map all provided URLs and combine results
        # 映射所有提供的 URL 并合并结果
        combined_links = []
        for url in urls:
            result = app.map_url(url, params=params)
            if isinstance(result, dict) and "links" in result:
                combined_links.extend(result["links"])

        # 构建映射结果
        map_result = {"success": True, "links": combined_links}

        return Data(data=map_result)
