from enum import Enum

import httpx
from langchain_core.tools import StructuredTool, ToolException
from pydantic import BaseModel, Field

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import BoolInput, DropdownInput, IntInput, MessageTextInput, SecretStrInput
from lfx.log.logger import logger
from lfx.schema.data import Data

# Add at the top with other constants
# 每个来源的最大内容分块数
MAX_CHUNKS_PER_SOURCE = 3


# Tavily 搜索深度枚举，用于控制搜索的详细程度
class TavilySearchDepth(Enum):
    BASIC = "basic"
    ADVANCED = "advanced"


# Tavily 搜索主题枚举，用于限定搜索的类别范围
class TavilySearchTopic(Enum):
    GENERAL = "general"
    NEWS = "news"


# Tavily 搜索时间范围枚举，用于按时间过滤搜索结果
class TavilySearchTimeRange(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


# Tavily 搜索的参数验证模型，定义了所有可配置的搜索参数及其默认值和约束
class TavilySearchSchema(BaseModel):
    query: str = Field(..., description="The search query you want to execute with Tavily.")
    search_depth: TavilySearchDepth = Field(TavilySearchDepth.BASIC, description="The depth of the search.")
    topic: TavilySearchTopic = Field(TavilySearchTopic.GENERAL, description="The category of the search.")
    max_results: int = Field(5, description="The maximum number of search results to return.")
    include_images: bool = Field(default=False, description="Include a list of query-related images in the response.")
    include_answer: bool = Field(default=False, description="Include a short answer to original query.")
    chunks_per_source: int = Field(
        default=MAX_CHUNKS_PER_SOURCE,
        description=(
            "The number of content chunks to retrieve from each source (max 500 chars each). Only for advanced search."
        ),
        ge=1,
        le=MAX_CHUNKS_PER_SOURCE,
    )
    include_domains: list[str] = Field(
        default=[],
        description="A list of domains to specifically include in the search results.",
    )
    exclude_domains: list[str] = Field(
        default=[],
        description="A list of domains to specifically exclude from the search results.",
    )
    include_raw_content: bool = Field(
        default=False,
        description="Include the cleaned and parsed HTML content of each search result.",
    )
    days: int = Field(
        default=7,
        description="Number of days back from the current date to include. Only available if topic is news.",
        ge=1,
    )
    time_range: TavilySearchTimeRange | None = Field(
        default=None,
        description="The time range back from the current date to filter results.",
    )


# Tavily 搜索工具组件，封装了 Tavily Search API，可用于独立搜索或作为 Agent 工具
class TavilySearchToolComponent(LCToolComponent):
    display_name = "Tavily Search API"
    description = """**Tavily Search API** is a search engine optimized for LLMs and RAG, \
        aimed at efficient, quick, and persistent search results. It can be used independently or as an agent tool.

Note: Check 'Advanced' for all options.
"""
    icon = "TavilyIcon"
    name = "TavilyAISearch"
    documentation = "https://docs.tavily.com/"
    legacy = True
    replacement = ["tavily.TavilySearchComponent"]

    # 组件输入参数定义
    inputs = [
        # Tavily API 密钥，必填项，用于身份认证
        SecretStrInput(
            name="api_key",
            display_name="Tavily API Key",
            required=True,
            info="Your Tavily API Key.",
        ),
        # 搜索查询文本，用户输入的搜索关键词
        MessageTextInput(
            name="query",
            display_name="Search Query",
            info="The search query you want to execute with Tavily.",
        ),
        # 搜索深度选择：basic（基础）或 advanced（高级），高级模式返回更多内容分块
        DropdownInput(
            name="search_depth",
            display_name="Search Depth",
            info="The depth of the search.",
            options=list(TavilySearchDepth),
            value=TavilySearchDepth.ADVANCED,
            advanced=True,
        ),
        # 每个来源的内容分块数量（1-3），仅在高级搜索模式下生效
        IntInput(
            name="chunks_per_source",
            display_name="Chunks Per Source",
            info=("The number of content chunks to retrieve from each source (1-3). Only works with advanced search."),
            value=MAX_CHUNKS_PER_SOURCE,
            advanced=True,
        ),
        # 搜索主题分类：general（通用）或 news（新闻）
        DropdownInput(
            name="topic",
            display_name="Search Topic",
            info="The category of the search.",
            options=list(TavilySearchTopic),
            value=TavilySearchTopic.GENERAL,
            advanced=True,
        ),
        # 回溯天数，仅在新闻主题下有效
        IntInput(
            name="days",
            display_name="Days",
            info="Number of days back from current date to include. Only available with news topic.",
            value=7,
            advanced=True,
        ),
        # 最大返回结果数
        IntInput(
            name="max_results",
            display_name="Max Results",
            info="The maximum number of search results to return.",
            value=5,
            advanced=True,
        ),
        # 是否包含对原始查询的简短回答
        BoolInput(
            name="include_answer",
            display_name="Include Answer",
            info="Include a short answer to original query.",
            value=True,
            advanced=True,
        ),
        # 时间范围过滤选项
        DropdownInput(
            name="time_range",
            display_name="Time Range",
            info="The time range back from the current date to filter results.",
            options=list(TavilySearchTimeRange),
            value=None,
            advanced=True,
        ),
        # 是否在结果中包含相关图片列表
        BoolInput(
            name="include_images",
            display_name="Include Images",
            info="Include a list of query-related images in the response.",
            value=True,
            advanced=True,
        ),
        # 指定包含的域名列表（逗号分隔），用于缩小搜索范围
        MessageTextInput(
            name="include_domains",
            display_name="Include Domains",
            info="Comma-separated list of domains to include in the search results.",
            advanced=True,
        ),
        # 指定排除的域名列表（逗号分隔），用于排除特定网站
        MessageTextInput(
            name="exclude_domains",
            display_name="Exclude Domains",
            info="Comma-separated list of domains to exclude from the search results.",
            advanced=True,
        ),
        # 是否包含搜索结果页面的原始 HTML 内容（已清洗和解析）
        BoolInput(
            name="include_raw_content",
            display_name="Include Raw Content",
            info="Include the cleaned and parsed HTML content of each search result.",
            value=False,
            advanced=True,
        ),
    ]

    # 执行模型搜索，将输入参数转换为枚举类型并调用 Tavily API
    def run_model(self) -> list[Data]:
        # Convert string values to enum instances with validation
        # 将搜索深度参数转换为 TavilySearchDepth 枚举实例
        try:
            search_depth_enum = (
                self.search_depth
                if isinstance(self.search_depth, TavilySearchDepth)
                else TavilySearchDepth(str(self.search_depth).lower())
            )
        except ValueError as e:
            error_message = f"Invalid search depth value: {e!s}"
            self.status = error_message
            return [Data(data={"error": error_message})]

        # 将搜索主题参数转换为 TavilySearchTopic 枚举实例
        try:
            topic_enum = (
                self.topic if isinstance(self.topic, TavilySearchTopic) else TavilySearchTopic(str(self.topic).lower())
            )
        except ValueError as e:
            error_message = f"Invalid topic value: {e!s}"
            self.status = error_message
            return [Data(data={"error": error_message})]

        # 将时间范围参数转换为 TavilySearchTimeRange 枚举实例（可选）
        try:
            time_range_enum = (
                self.time_range
                if isinstance(self.time_range, TavilySearchTimeRange)
                else TavilySearchTimeRange(str(self.time_range).lower())
                if self.time_range
                else None
            )
        except ValueError as e:
            error_message = f"Invalid time range value: {e!s}"
            self.status = error_message
            return [Data(data={"error": error_message})]

        # Initialize domain variables as None
        # 初始化域名过滤变量
        include_domains = None
        exclude_domains = None

        # Only process domains if they're provided
        # 仅在用户提供了域名时进行解析处理（逗号分隔的字符串转换为列表）
        if self.include_domains:
            include_domains = [domain.strip() for domain in self.include_domains.split(",") if domain.strip()]

        if self.exclude_domains:
            exclude_domains = [domain.strip() for domain in self.exclude_domains.split(",") if domain.strip()]

        # 调用底层的 Tavily 搜索方法并返回结果
        return self._tavily_search(
            self.query,
            search_depth=search_depth_enum,
            topic=topic_enum,
            max_results=self.max_results,
            include_images=self.include_images,
            include_answer=self.include_answer,
            chunks_per_source=self.chunks_per_source,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            include_raw_content=self.include_raw_content,
            days=self.days,
            time_range=time_range_enum,
        )

    # 构建 LangChain StructuredTool 实例，使搜索功能可以作为 Agent 工具使用
    def build_tool(self) -> Tool:
        return StructuredTool.from_function(
            name="tavily_search",
            description="Perform a web search using the Tavily API.",
            func=self._tavily_search,
            args_schema=TavilySearchSchema,
        )

    # Tavily 搜索的核心实现方法，负责发送 HTTP 请求并处理响应结果
    def _tavily_search(
        self,
        query: str,
        *,
        search_depth: TavilySearchDepth = TavilySearchDepth.BASIC,
        topic: TavilySearchTopic = TavilySearchTopic.GENERAL,
        max_results: int = 5,
        include_images: bool = False,
        include_answer: bool = False,
        chunks_per_source: int = MAX_CHUNKS_PER_SOURCE,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        include_raw_content: bool = False,
        days: int = 7,
        time_range: TavilySearchTimeRange | None = None,
    ) -> list[Data]:
        # Validate enum values
        # 验证搜索深度枚举值类型
        if not isinstance(search_depth, TavilySearchDepth):
            msg = f"Invalid search_depth value: {search_depth}"
            raise TypeError(msg)
        # 验证搜索主题枚举值类型
        if not isinstance(topic, TavilySearchTopic):
            msg = f"Invalid topic value: {topic}"
            raise TypeError(msg)

        # Validate chunks_per_source range
        # 验证每个来源的内容分块数在合法范围内（1-3）
        if not 1 <= chunks_per_source <= MAX_CHUNKS_PER_SOURCE:
            msg = f"chunks_per_source must be between 1 and {MAX_CHUNKS_PER_SOURCE}, got {chunks_per_source}"
            raise ValueError(msg)

        # Validate days is positive
        # 验证回溯天数为正整数
        if days < 1:
            msg = f"days must be greater than or equal to 1, got {days}"
            raise ValueError(msg)

        try:
            # Tavily API 搜索接口地址
            url = "https://api.tavily.com/search"
            # 设置 HTTP 请求头
            headers = {
                "content-type": "application/json",
                "accept": "application/json",
            }
            # 构造请求负载，将各参数映射到 API 所需的字段
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth.value,
                "topic": topic.value,
                "max_results": max_results,
                "include_images": include_images,
                "include_answer": include_answer,
                # chunks_per_source 仅在高级搜索模式下传入
                "chunks_per_source": chunks_per_source if search_depth == TavilySearchDepth.ADVANCED else None,
                "include_domains": include_domains if include_domains else None,
                "exclude_domains": exclude_domains if exclude_domains else None,
                "include_raw_content": include_raw_content,
                # days 参数仅在新闻主题下传入
                "days": days if topic == TavilySearchTopic.NEWS else None,
                "time_range": time_range.value if time_range else None,
            }

            # 使用 httpx 发送 POST 请求，超时时间为 90 秒
            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, json=payload, headers=headers)

            # 如果响应状态码不是 2xx 则抛出异常
            response.raise_for_status()
            search_results = response.json()

            # 将 API 返回的搜索结果转换为 Data 对象列表
            data_results = [
                Data(
                    data={
                        "title": result.get("title"),
                        "url": result.get("url"),
                        "content": result.get("content"),
                        "score": result.get("score"),
                        "raw_content": result.get("raw_content") if include_raw_content else None,
                    }
                )
                for result in search_results.get("results", [])
            ]

            # 如果启用了包含答案选项且 API 返回了答案，则将其插入到结果列表的开头
            if include_answer and search_results.get("answer"):
                data_results.insert(0, Data(data={"answer": search_results["answer"]}))

            # 如果启用了包含图片选项且 API 返回了图片列表，则将其追加到结果列表末尾
            if include_images and search_results.get("images"):
                data_results.append(Data(data={"images": search_results["images"]}))

            # 设置组件状态为搜索结果列表
            self.status = data_results  # type: ignore[assignment]

        # 处理请求超时异常
        except httpx.TimeoutException as e:
            error_message = "Request timed out (90s). Please try again or adjust parameters."
            logger.error(f"Timeout error: {e}")
            self.status = error_message
            raise ToolException(error_message) from e
        # 处理 HTTP 状态码错误（如 401 认证失败、429 请求过多等）
        except httpx.HTTPStatusError as e:
            error_message = f"HTTP error: {e.response.status_code} - {e.response.text}"
            logger.debug(error_message)
            self.status = error_message
            raise ToolException(error_message) from e
        # 处理其他未预期的异常
        except Exception as e:
            error_message = f"Unexpected error: {e}"
            logger.debug("Error running Tavily Search", exc_info=True)
            self.status = error_message
            raise ToolException(error_message) from e
        return data_results
