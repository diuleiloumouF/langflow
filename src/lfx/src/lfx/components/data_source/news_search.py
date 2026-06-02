from urllib.parse import quote_plus

import pandas as pd
import requests
from bs4 import BeautifulSoup

from lfx.custom import Component
from lfx.io import IntInput, MessageTextInput, Output
from lfx.schema import DataFrame


# 新闻搜索组件 - 通过 Google News RSS 搜索新闻文章
class NewsSearchComponent(Component):
    """新闻搜索组件，通过 Google News 的 RSS 源搜索新闻文章并返回结构化数据。"""

    # 组件显示名称
    display_name = "News Search"
    # 组件描述：通过 RSS 搜索 Google 新闻，返回清洗后的文章数据
    description = "Searches Google News via RSS. Returns clean article data."
    documentation: str = "https://docs.langflow.org/web-search"
    # 组件图标
    icon = "newspaper"
    # 组件内部名称
    name = "NewsSearch"
    # 标记为遗留组件，建议使用新的 WebSearch 组件替代
    legacy = True
    replacement = "data.WebSearch"

    # 组件输入参数定义
    inputs = [
        MessageTextInput(
            name="query",
            # 搜索关键词输入
            display_name="Search Query",
            info="Search keywords for news articles.",
            # 工具模式下可作为工具调用
            tool_mode=True,
            required=True,
        ),
        MessageTextInput(
            name="hl",
            # 语言代码参数，如 en-US、fr、de，影响搜索结果的语言
            display_name="Language (hl)",
            info="Language code, e.g. en-US, fr, de. Default: en-US.",
            tool_mode=False,
            input_types=[],
            required=False,
            advanced=True,
        ),
        MessageTextInput(
            name="gl",
            # 国家代码参数，如 US、FR、DE，影响搜索结果的地区
            display_name="Country (gl)",
            info="Country code, e.g. US, FR, DE. Default: US.",
            tool_mode=False,
            input_types=[],
            required=False,
            advanced=True,
        ),
        MessageTextInput(
            name="ceid",
            # 国家:语言组合代码，如 US:en、FR:fr
            display_name="Country:Language (ceid)",
            info="e.g. US:en, FR:fr. Default: US:en.",
            tool_mode=False,
            value="US:en",
            input_types=[],
            required=False,
            advanced=True,
        ),
        MessageTextInput(
            name="topic",
            # 新闻主题分类，如世界、商业、科技、体育等
            display_name="Topic",
            info="One of: WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SCIENCE, SPORTS, HEALTH.",
            tool_mode=False,
            input_types=[],
            required=False,
            advanced=True,
        ),
        MessageTextInput(
            name="location",
            # 基于地理位置的新闻搜索，如城市、州或国家
            display_name="Location (Geo)",
            info="City, state, or country for location-based news. Leave blank for keyword search.",
            tool_mode=False,
            input_types=[],
            required=False,
            advanced=True,
        ),
        IntInput(
            name="timeout",
            # 请求超时时间（秒）
            display_name="Timeout",
            info="Timeout for the request in seconds.",
            value=5,
            required=False,
            advanced=True,
        ),
    ]

    # 输出参数：返回新闻文章的 DataFrame
    outputs = [Output(name="articles", display_name="News Articles", method="search_news")]

    def search_news(self) -> DataFrame:
        """搜索新闻的主方法，根据输入参数构建 RSS URL 并获取新闻文章数据。"""
        # 设置默认值
        hl = getattr(self, "hl", None) or "en-US"
        gl = getattr(self, "gl", None) or "US"
        ceid = getattr(self, "ceid", None) or f"{gl}:{hl.split('-')[0]}"
        topic = getattr(self, "topic", None)
        location = getattr(self, "location", None)
        query = getattr(self, "query", None)

        # 根据不同搜索模式构建 RSS URL
        if topic:
            # 按主题搜索：构建主题 RSS 订阅地址
            base_url = f"https://news.google.com/rss/headlines/section/topic/{quote_plus(topic.upper())}"
            params = f"?hl={hl}&gl={gl}&ceid={ceid}"
            rss_url = base_url + params
        elif location:
            # 按地理位置搜索：构建地理 RSS 订阅地址
            base_url = f"https://news.google.com/rss/headlines/section/geo/{quote_plus(location)}"
            params = f"?hl={hl}&gl={gl}&ceid={ceid}"
            rss_url = base_url + params
        elif query:
            # 关键词搜索：构建关键词搜索 RSS 订阅地址
            base_url = "https://news.google.com/rss/search?q="
            query_parts = [query]
            query_encoded = quote_plus(" ".join(query_parts))
            params = f"&hl={hl}&gl={gl}&ceid={ceid}"
            rss_url = f"{base_url}{query_encoded}{params}"
        else:
            # 未提供搜索条件，返回错误提示
            self.status = "No search query, topic, or location provided."
            self.log(self.status)
            return DataFrame(
                pd.DataFrame(
                    [
                        {
                            "title": "Error",
                            "link": "",
                            "published": "",
                            "summary": "No search query, topic, or location provided.",
                        }
                    ]
                )
            )

        try:
            # 发送 HTTP 请求获取 RSS 内容
            response = requests.get(rss_url, timeout=self.timeout)
            response.raise_for_status()
            # 使用 BeautifulSoup 解析 XML 格式的 RSS 数据
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")
        except requests.RequestException as e:
            # 处理网络请求错误
            self.status = f"Failed to fetch news: {e}"
            self.log(self.status)
            return DataFrame(pd.DataFrame([{"title": "Error", "link": "", "published": "", "summary": str(e)}]))
        except (AttributeError, ValueError, TypeError) as e:
            # 处理解析过程中的意外错误
            self.status = f"Unexpected error: {e!s}"
            self.log(self.status)
            return DataFrame(pd.DataFrame([{"title": "Error", "link": "", "published": "", "summary": str(e)}]))

        # 没有找到新闻文章时返回空结果
        if not items:
            self.status = "No news articles found."
            self.log(self.status)
            return DataFrame(pd.DataFrame([{"title": "No articles found", "link": "", "published": "", "summary": ""}]))

        # 解析每篇新闻文章的标题、链接、发布时间和摘要
        articles = []
        for item in items:
            try:
                # 提取并清洗 HTML 格式的标题
                title = self.clean_html(item.title.text if item.title else "")
                link = item.link.text if item.link else ""
                published = item.pubDate.text if item.pubDate else ""
                # 提取并清洗 HTML 格式的摘要
                summary = self.clean_html(item.description.text if item.description else "")
                articles.append({"title": title, "link": link, "published": published, "summary": summary})
            except (AttributeError, ValueError, TypeError) as e:
                # 跳过解析失败的文章，记录日志后继续处理下一条
                self.log(f"Error parsing article: {e!s}")
                continue

        # 将文章列表转换为 DataFrame 返回
        df_articles = pd.DataFrame(articles)
        self.log(f"Found {len(df_articles)} articles.")
        return DataFrame(df_articles)

    def clean_html(self, html_string: str) -> str:
        """清洗 HTML 字符串，移除标签并返回纯文本内容。"""
        return BeautifulSoup(html_string, "html.parser").get_text(separator=" ", strip=True)
