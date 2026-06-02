# 数据处理相关依赖
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Langflow 组件框架导入
from lfx.custom import Component
from lfx.io import IntInput, MessageTextInput, Output
from lfx.log.logger import logger
from lfx.schema import DataFrame


# RSS 阅读器组件：获取并解析 RSS 订阅源，返回文章列表
class RSSReaderComponent(Component):
    # 组件显示名称
    display_name = "RSS Reader"
    # 组件描述
    description = "Fetches and parses an RSS feed."
    documentation: str = "https://docs.langflow.org/web-search"
    # 组件图标
    icon = "rss"
    # 组件内部名称
    name = "RSSReaderSimple"
    # 标记为旧版组件，不再维护
    legacy = True
    # 推荐的替代组件
    replacement = "data.WebSearch"

    # 组件输入定义
    inputs = [
        # RSS 订阅源的 URL 地址（必填）
        MessageTextInput(
            name="rss_url",
            display_name="RSS Feed URL",
            info="URL of the RSS feed to parse.",
            tool_mode=True,
            required=True,
        ),
        # 请求超时时间（高级参数，默认 5 秒）
        IntInput(
            name="timeout",
            display_name="Timeout",
            info="Timeout for the RSS feed request.",
            value=5,
            advanced=True,
        ),
    ]

    # 组件输出定义：文章列表，由 read_rss 方法生成
    outputs = [Output(name="articles", display_name="Articles", method="read_rss")]

    # 读取并解析 RSS 订阅源，返回包含文章信息的 DataFrame
    def read_rss(self) -> DataFrame:
        try:
            # 发送 HTTP GET 请求获取 RSS 内容
            response = requests.get(self.rss_url, timeout=self.timeout)
            # 检查 HTTP 响应状态码，非 2xx 则抛出异常
            response.raise_for_status()
            # 检查响应内容是否为空
            if not response.content.strip():
                msg = "Empty response received"
                raise ValueError(msg)
            # Check if the response is valid XML
            try:
                # 尝试用 BeautifulSoup 解析 XML 格式，验证内容有效性
                BeautifulSoup(response.content, "xml")
            except Exception as e:
                msg = f"Invalid XML response: {e}"
                raise ValueError(msg) from e
            # 正式解析 XML 内容
            soup = BeautifulSoup(response.content, "xml")
            # 提取所有 <item> 标签，每个代表一篇文章
            items = soup.find_all("item")
        # 捕获请求异常或解析异常，将错误信息返回为错误行
        except (requests.RequestException, ValueError) as e:
            self.status = f"Failed to fetch RSS: {e}"
            return DataFrame(pd.DataFrame([{"title": "Error", "link": "", "published": "", "summary": str(e)}]))

        # 从每个 item 中提取文章的标题、链接、发布时间和摘要
        articles = [
            {
                "title": item.title.text if item.title else "",
                "link": item.link.text if item.link else "",
                "published": item.pubDate.text if item.pubDate else "",
                "summary": item.description.text if item.description else "",
            }
            for item in items
        ]

        # Ensure the DataFrame has the correct columns even if empty
        # 构建 DataFrame，即使 articles 为空也能保证列结构正确
        df_articles = pd.DataFrame(articles, columns=["title", "link", "published", "summary"])
        logger.info(f"Fetched {len(df_articles)} articles.")
        return DataFrame(df_articles)
