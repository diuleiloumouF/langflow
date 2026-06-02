# HTTP 客户端库，用于向 Tavily API 发送请求
import httpx

# Langflow 组件基类
from lfx.custom.custom_component.component import Component

# 组件输入类型：布尔输入、下拉框输入、整数输入、消息文本输入、密钥字符串输入
from lfx.inputs.inputs import BoolInput, DropdownInput, IntInput, MessageTextInput, SecretStrInput

# 日志记录器
from lfx.log.logger import logger

# 数据模型，用于封装搜索结果
from lfx.schema.data import Data

# DataFrame 数据模型，用于表格化输出搜索结果
from lfx.schema.dataframe import DataFrame

# 输出字段基类，用于定义组件的输出接口
from lfx.template.field.base import Output


# Tavily 搜索组件：封装 Tavily Search API，提供针对 LLM 和 RAG 优化的搜索功能
class TavilySearchComponent(Component):
    # 组件在画布上显示的名称
    display_name = "Tavily Search API"
    # 组件的描述信息
    description = """**Tavily Search** is a search engine optimized for LLMs and RAG, \
        aimed at efficient, quick, and persistent search results."""
    # 组件图标
    icon = "TavilyIcon"

    # 组件的输入参数定义列表
    inputs = [
        # Tavily API 密钥（密钥类型输入，不会明文显示）
        SecretStrInput(
            name="api_key",
            display_name="Tavily API Key",
            required=True,
            info="Your Tavily API Key.",
        ),
        # 搜索查询文本输入，支持 tool_mode 以在工具模式下使用
        MessageTextInput(
            name="query",
            display_name="Search Query",
            info="The search query you want to execute with Tavily.",
            tool_mode=True,
        ),
        # 搜索深度选择：basic（基础）或 advanced（高级）
        DropdownInput(
            name="search_depth",
            display_name="Search Depth",
            info="The depth of the search.",
            options=["basic", "advanced"],
            value="advanced",
            advanced=True,
        ),
        # 每个来源的内容块数量（仅高级搜索有效，范围 1-3）
        IntInput(
            name="chunks_per_source",
            display_name="Chunks Per Source",
            info=("The number of content chunks to retrieve from each source (1-3). Only works with advanced search."),
            value=3,
            advanced=True,
        ),
        # 搜索主题分类：general（通用）或 news（新闻）
        DropdownInput(
            name="topic",
            display_name="Search Topic",
            info="The category of the search.",
            options=["general", "news"],
            value="general",
            advanced=True,
        ),
        # 回溯天数，仅在 news 主题下有效
        IntInput(
            name="days",
            display_name="Days",
            info="Number of days back from current date to include. Only available with news topic.",
            value=7,
            advanced=True,
        ),
        # 最大返回结果数量
        IntInput(
            name="max_results",
            display_name="Max Results",
            info="The maximum number of search results to return.",
            value=5,
            advanced=True,
        ),
        # 是否在结果中包含对原始查询的简短回答
        BoolInput(
            name="include_answer",
            display_name="Include Answer",
            info="Include a short answer to original query.",
            value=True,
            advanced=True,
        ),
        # 时间范围过滤：按天、周、月、年筛选结果
        DropdownInput(
            name="time_range",
            display_name="Time Range",
            info="The time range back from the current date to filter results.",
            options=["day", "week", "month", "year"],
            value=None,  # Default to None to make it optional
            advanced=True,
        ),
        # 是否在结果中包含与查询相关的图片列表
        BoolInput(
            name="include_images",
            display_name="Include Images",
            info="Include a list of query-related images in the response.",
            value=True,
            advanced=True,
        ),
        # 逗号分隔的域名白名单，仅从这些域名获取搜索结果
        MessageTextInput(
            name="include_domains",
            display_name="Include Domains",
            info="Comma-separated list of domains to include in the search results.",
            advanced=True,
        ),
        # 逗号分隔的域名黑名单，排除这些域名的搜索结果
        MessageTextInput(
            name="exclude_domains",
            display_name="Exclude Domains",
            info="Comma-separated list of domains to exclude from the search results.",
            advanced=True,
        ),
        # 是否包含每个搜索结果的原始 HTML 内容（经清洗和解析后）
        BoolInput(
            name="include_raw_content",
            display_name="Include Raw Content",
            info="Include the cleaned and parsed HTML content of each search result.",
            value=False,
            advanced=True,
        ),
    ]

    # 组件的输出定义：将搜索结果以表格（DataFrame）形式输出
    outputs = [
        Output(display_name="Table", name="dataframe", method="fetch_content_dataframe"),
    ]

    # 执行 Tavily 搜索并返回 Data 对象列表
    def fetch_content(self) -> list[Data]:
        try:
            # Only process domains if they're provided
            # 初始化域名过滤参数（仅在用户提供了域名时才处理）
            include_domains = None
            exclude_domains = None

            if self.include_domains:
                # 将逗号分隔的包含域名字符串解析为列表，去除空白
                include_domains = [domain.strip() for domain in self.include_domains.split(",") if domain.strip()]

            if self.exclude_domains:
                # 将逗号分隔的排除域名字符串解析为列表，去除空白
                exclude_domains = [domain.strip() for domain in self.exclude_domains.split(",") if domain.strip()]

            # Tavily 搜索 API 端点
            url = "https://api.tavily.com/search"
            # 请求头：指定内容类型和接受的响应格式为 JSON
            headers = {
                "content-type": "application/json",
                "accept": "application/json",
            }

            # 构建请求负载，包含所有搜索参数
            payload = {
                "api_key": self.api_key,
                "query": self.query,
                "search_depth": self.search_depth,
                "topic": self.topic,
                "max_results": self.max_results,
                "include_images": self.include_images,
                "include_answer": self.include_answer,
                "include_raw_content": self.include_raw_content,
                "days": self.days,
                "time_range": self.time_range,
            }

            # Only add domains to payload if they exist and have values
            # 仅在有域名白名单时将其加入请求负载
            if include_domains:
                payload["include_domains"] = include_domains
            # 仅在有域名黑名单时将其加入请求负载
            if exclude_domains:
                payload["exclude_domains"] = exclude_domains

            # Add conditional parameters only if they should be included
            # 高级搜索模式下才添加 chunks_per_source 参数
            if self.search_depth == "advanced" and self.chunks_per_source:
                payload["chunks_per_source"] = self.chunks_per_source

            # 新闻主题下才添加 days 回溯天数参数
            if self.topic == "news" and self.days:
                payload["days"] = int(self.days)  # Ensure days is an integer

            # Add time_range if it's set
            # 仅在 time_range 有值时才添加该过滤参数
            if hasattr(self, "time_range") and self.time_range:
                payload["time_range"] = self.time_range

            # Add timeout handling
            # 创建 HTTP 客户端并发送 POST 请求，超时时间 90 秒
            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, json=payload, headers=headers)

            # 检查 HTTP 响应状态码，非 2xx 时抛出异常
            response.raise_for_status()
            search_results = response.json()

            data_results = []

            # 如果启用了包含回答且 API 返回了回答，则将其添加到结果中
            if self.include_answer and search_results.get("answer"):
                data_results.append(Data(text=search_results["answer"]))

            # 遍历搜索结果列表，将每条结果封装为 Data 对象
            for result in search_results.get("results", []):
                content = result.get("content", "")
                result_data = {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "content": content,
                    "score": result.get("score"),
                }
                # 仅在启用原始内容时添加 raw_content 字段
                if self.include_raw_content:
                    result_data["raw_content"] = result.get("raw_content")

                data_results.append(Data(text=content, data=result_data))

            # 如果启用了包含图片且 API 返回了图片，则将图片信息添加到结果中
            if self.include_images and search_results.get("images"):
                data_results.append(Data(text="Images found", data={"images": search_results["images"]}))

        # 捕获请求超时异常
        except httpx.TimeoutException:
            error_message = "Request timed out (90s). Please try again or adjust parameters."
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        # 捕获 HTTP 状态码错误（如 4xx、5xx）
        except httpx.HTTPStatusError as exc:
            error_message = f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        # 捕获其他网络请求错误（如连接失败、DNS 解析失败等）
        except httpx.RequestError as exc:
            error_message = f"Request error occurred: {exc}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        # 捕获响应数据解析错误（如 JSON 格式不合法）
        except ValueError as exc:
            error_message = f"Invalid response format: {exc}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        else:
            # 搜索成功，将结果保存到组件状态并返回
            self.status = data_results
            return data_results

    # 将搜索结果转换为 DataFrame 表格格式输出
    def fetch_content_dataframe(self) -> DataFrame:
        data = self.fetch_content()
        return DataFrame(data)
