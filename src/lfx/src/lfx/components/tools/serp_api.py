# 导入类型注解
from typing import Any

# LangChain 社区工具：SerpAPI 搜索工具封装
from langchain_community.utilities.serpapi import SerpAPIWrapper

# LangChain 工具基础类和异常类
from langchain_core.tools import StructuredTool, ToolException

# Pydantic 数据模型基类和字段定义
from pydantic import BaseModel, Field

# LangChain 工具组件基类
from lfx.base.langchain_utilities.model import LCToolComponent

# 工具类型定义
from lfx.field_typing import Tool

# 组件输入类型定义
from lfx.inputs.inputs import DictInput, IntInput, MultilineInput, SecretStrInput

# 日志记录器
from lfx.log.logger import logger

# 数据模型，用于组件间数据传递
from lfx.schema.data import Data


# SerpAPI 搜索参数的数据模型，用于定义搜索工具的输入参数结构
class SerpAPISchema(BaseModel):
    """Schema for SerpAPI search parameters."""

    # 搜索查询字符串（必填）
    query: str = Field(..., description="The search query")
    # 附加搜索参数，包括搜索引擎、域名、地区和语言设置
    params: dict[str, Any] | None = Field(
        default={
            "engine": "google",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
        },
        description="Additional search parameters",
    )
    # 最大返回结果数量，默认为 5
    max_results: int = Field(5, description="Maximum number of results to return")
    # 每个结果摘要的最大长度，默认为 100 字符
    max_snippet_length: int = Field(100, description="Maximum length of each result snippet")


# SerpAPI 搜索工具组件，提供网页搜索功能，支持结果数量限制和摘要截断
# 该组件已被标记为遗留版本（legacy），建议使用 serpapi.Serp 替代
class SerpAPIComponent(LCToolComponent):
    # 组件显示名称
    display_name = "Serp Search API"
    # 组件描述
    description = "Call Serp Search API with result limiting"
    # 组件内部名称，用于代码引用
    name = "SerpAPI"
    # 组件图标名称
    icon = "SerpSearch"
    # 标记为遗留组件，不推荐新用户使用
    legacy = True
    # 推荐的替代组件列表
    replacement = ["serpapi.Serp"]

    # 组件输入参数定义
    inputs = [
        # SerpAPI 密钥，用于身份验证（必填）
        SecretStrInput(name="serpapi_api_key", display_name="SerpAPI API Key", required=True),
        # 搜索查询输入框
        MultilineInput(
            name="input_value",
            display_name="Input",
        ),
        # 附加搜索参数（高级选项），支持多个参数字典
        DictInput(name="search_params", display_name="Parameters", advanced=True, is_list=True),
        # 最大返回结果数量（高级选项），默认 5
        IntInput(name="max_results", display_name="Max Results", value=5, advanced=True),
        # 摘要最大长度（高级选项），默认 100 字符
        IntInput(name="max_snippet_length", display_name="Max Snippet Length", value=100, advanced=True),
    ]

    # 构建 SerpAPI 封装器，支持自定义搜索参数
    def _build_wrapper(self, params: dict[str, Any] | None = None) -> SerpAPIWrapper:
        """Build a SerpAPIWrapper with the provided parameters."""
        params = params or {}
        if params:
            return SerpAPIWrapper(
                serpapi_api_key=self.serpapi_api_key,
                params=params,
            )
        return SerpAPIWrapper(serpapi_api_key=self.serpapi_api_key)

    # 构建搜索工具，返回可调用的 StructuredTool 实例
    def build_tool(self) -> Tool:
        # 使用配置的搜索参数构建 SerpAPI 封装器
        wrapper = self._build_wrapper(self.search_params)

        # 内部搜索函数，执行实际的搜索操作并限制结果
        def search_func(
            query: str, params: dict[str, Any] | None = None, max_results: int = 5, max_snippet_length: int = 100
        ) -> list[dict[str, Any]]:
            try:
                # 使用默认封装器或根据传入参数创建新的封装器
                local_wrapper = wrapper
                if params:
                    local_wrapper = self._build_wrapper(params)

                # 执行搜索并获取完整结果
                full_results = local_wrapper.results(query)
                # 提取自然搜索结果并限制数量
                organic_results = full_results.get("organic_results", [])[:max_results]

                # 处理每个结果，截断标题和摘要到指定长度
                limited_results = []
                for result in organic_results:
                    limited_result = {
                        "title": result.get("title", "")[:max_snippet_length],
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", "")[:max_snippet_length],
                    }
                    limited_results.append(limited_result)

            except Exception as e:
                # 记录错误日志并抛出工具异常
                error_message = f"Error in SerpAPI search: {e!s}"
                logger.debug(error_message)
                raise ToolException(error_message) from e
            return limited_results

        # 从搜索函数创建结构化工具实例
        tool = StructuredTool.from_function(
            name="serp_search_api",
            description="Search for recent results using SerpAPI with result limiting",
            func=search_func,
            args_schema=SerpAPISchema,
        )

        # 更新组件状态
        self.status = "SerpAPI Tool created"
        return tool

    # 执行搜索模型，返回搜索结果列表
    def run_model(self) -> list[Data]:
        # 构建搜索工具
        tool = self.build_tool()
        try:
            # 使用组件输入参数调用搜索工具
            results = tool.run(
                {
                    "query": self.input_value,
                    "params": self.search_params or {},
                    "max_results": self.max_results,
                    "max_snippet_length": self.max_snippet_length,
                }
            )

            # 将搜索结果转换为 Data 对象列表
            data_list = [Data(data=result, text=result.get("snippet", "")) for result in results]

        except Exception as e:  # noqa: BLE001
            # 记录错误并返回包含错误信息的 Data 对象
            logger.debug("Error running SerpAPI", exc_info=True)
            self.status = f"Error: {e}"
            return [Data(data={"error": str(e)}, text=str(e))]

        # 设置组件状态为结果列表
        self.status = data_list  # type: ignore[assignment]
        return data_list
