# typing 模块：提供类型注解支持
from typing import Any

# LangChain 社区工具：SerpAPI 搜索封装
from langchain_community.utilities.serpapi import SerpAPIWrapper

# LangChain 核心工具：工具异常类
from langchain_core.tools import ToolException

# Pydantic：数据模型和字段验证
from pydantic import BaseModel, Field

# 自定义组件基类
from lfx.custom.custom_component.component import Component

# 组件输入类型定义
from lfx.inputs.inputs import DictInput, IntInput, MultilineInput, SecretStrInput

# 组件输出类型定义
from lfx.io import Output

# 日志记录器
from lfx.log.logger import logger

# 数据输出类型
from lfx.schema.data import Data

# 消息输出类型
from lfx.schema.message import Message


class SerpAPISchema(BaseModel):
    """Schema for SerpAPI search parameters.

    SerpAPI 搜索参数的 Pydantic 数据模型，用于验证和序列化搜索请求。
    """

    # 搜索查询字符串（必填）
    query: str = Field(..., description="The search query")
    # 额外的搜索参数，可选，默认使用 Google 搜索引擎配置
    params: dict[str, Any] | None = Field(
        default={
            "engine": "google",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
        },
        description="Additional search parameters",
    )
    # 返回结果的最大数量，默认为 5
    max_results: int = Field(5, description="Maximum number of results to return")
    # 每个结果摘要的最大长度，默认为 100 字符
    max_snippet_length: int = Field(100, description="Maximum length of each result snippet")


class SerpComponent(Component):
    """SerpAPI 搜索组件。

    通过 SerpAPI 执行网络搜索，支持结果数量限制和摘要长度截断。
    输出格式支持 JSON（结构化数据）和纯文本。
    """

    # 组件显示名称
    display_name = "Serp Search API"
    # 组件描述
    description = "Call Serp Search API with result limiting"
    # 组件内部名称标识
    name = "Serp"
    # 组件图标
    icon = "SerpSearch"

    # 组件输入定义
    inputs = [
        # SerpAPI 密钥（必填，敏感信息）
        SecretStrInput(name="serpapi_api_key", display_name="SerpAPI API Key", required=True),
        # 搜索查询输入（支持多行，工具模式下可用）
        MultilineInput(
            name="input_value",
            display_name="Input",
            tool_mode=True,
        ),
        # 额外搜索参数（高级选项，支持列表形式）
        DictInput(name="search_params", display_name="Parameters", advanced=True, is_list=True),
        # 最大返回结果数（高级选项，默认 5）
        IntInput(name="max_results", display_name="Max Results", value=5, advanced=True),
        # 摘要最大长度（高级选项，默认 100 字符）
        IntInput(name="max_snippet_length", display_name="Max Snippet Length", value=100, advanced=True),
    ]

    # 组件输出定义
    outputs = [
        # JSON 格式输出：结构化搜索结果
        Output(display_name="JSON", name="data", method="fetch_content"),
        # 文本格式输出：所有结果拼接为纯文本
        Output(display_name="Text", name="text", method="fetch_content_text"),
    ]

    def _build_wrapper(self, params: dict[str, Any] | None = None) -> SerpAPIWrapper:
        """Build a SerpAPIWrapper with the provided parameters.

        根据给定参数构建 SerpAPI 封装对象。
        如果未提供参数，则使用默认配置创建。
        """
        params = params or {}
        if params:
            return SerpAPIWrapper(
                serpapi_api_key=self.serpapi_api_key,
                params=params,
            )
        return SerpAPIWrapper(serpapi_api_key=self.serpapi_api_key)

    def run_model(self) -> list[Data]:
        """执行模型运行，委托给 fetch_content 方法。"""
        return self.fetch_content()

    def fetch_content(self) -> list[Data]:
        """执行搜索并返回结构化结果。

        通过 SerpAPI 执行搜索查询，将结果转换为 Data 对象列表。
        支持限制返回结果数量和截断摘要长度。
        """
        # 构建搜索封装对象
        wrapper = self._build_wrapper(self.search_params)

        def search_func(
            query: str, params: dict[str, Any] | None = None, max_results: int = 5, max_snippet_length: int = 100
        ) -> list[Data]:
            """执行搜索并返回 Data 对象列表。

            Args:
                query: 搜索查询字符串
                params: 额外的搜索参数
                max_results: 最大返回结果数
                max_snippet_length: 摘要最大长度

            Returns:
                包含搜索结果的 Data 对象列表
            """
            try:
                # 如果提供了额外参数，使用新参数创建封装对象
                local_wrapper = wrapper
                if params:
                    local_wrapper = self._build_wrapper(params)

                # 执行搜索获取完整结果
                full_results = local_wrapper.results(query)
                # 提取有机搜索结果并限制数量
                organic_results = full_results.get("organic_results", [])[:max_results]

                # 将结果转换为 Data 对象，截断标题和摘要
                limited_results = [
                    Data(
                        text=result.get("snippet", ""),
                        data={
                            "title": result.get("title", "")[:max_snippet_length],
                            "link": result.get("link", ""),
                            "snippet": result.get("snippet", "")[:max_snippet_length],
                        },
                    )
                    for result in organic_results
                ]

            except Exception as e:
                # 捕获异常，记录调试信息并抛出工具异常
                error_message = f"Error in SerpAPI search: {e!s}"
                logger.debug(error_message)
                raise ToolException(error_message) from e
            return limited_results

        # 使用输入参数执行搜索
        results = search_func(
            self.input_value,
            params=self.search_params,
            max_results=self.max_results,
            max_snippet_length=self.max_snippet_length,
        )
        # 保存搜索结果到状态（供 UI 显示）
        self.status = results
        return results

    def fetch_content_text(self) -> Message:
        """执行搜索并返回纯文本结果。

        将所有搜索结果的文本拼接为一个字符串，用换行符分隔。
        """
        # 获取结构化搜索结果
        data = self.fetch_content()
        # 拼接所有结果文本
        result_string = ""
        for item in data:
            result_string += item.text + "\n"
        # 保存文本结果到状态
        self.status = result_string
        # 返回消息对象
        return Message(text=result_string)
