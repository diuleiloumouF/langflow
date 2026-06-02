# LangChain 工具装饰器，用于将函数包装为工具
from langchain_core.tools import tool

# Metaphor（现 Exa）搜索 API 的 Python SDK
from metaphor_python import Metaphor

# 自定义组件基类
from lfx.custom.custom_component.component import Component

# 工具类型定义
from lfx.field_typing import Tool

# 组件输入输出类型定义
from lfx.io import BoolInput, IntInput, Output, SecretStrInput


# Exa Search 工具包组件，基于 Metaphor API 提供网页搜索和内容检索功能
class ExaSearchToolkit(Component):
    display_name = "Exa Search"
    # Exa Search 工具包，用于搜索和内容检索
    description = "Exa Search toolkit for search and content retrieval"
    documentation = "https://python.langchain.com/docs/integrations/tools/metaphor_search"
    beta = True
    name = "ExaSearch"
    icon = "ExaSearch"

    # 输入参数定义
    inputs = [
        # Exa Search API 密钥
        SecretStrInput(
            name="metaphor_api_key",
            display_name="Exa Search API Key",
            password=True,
        ),
        # 是否使用自动提示优化搜索查询
        BoolInput(
            name="use_autoprompt",
            display_name="Use Autoprompt",
            value=True,
        ),
        # 搜索返回的结果数量
        IntInput(
            name="search_num_results",
            display_name="Search Number of Results",
            value=5,
        ),
        # 相似搜索返回的结果数量
        IntInput(
            name="similar_num_results",
            display_name="Similar Number of Results",
            value=5,
        ),
    ]

    # 输出参数定义：返回工具列表
    outputs = [
        Output(name="tools", display_name="Tools", method="build_toolkit"),
    ]

    # 构建工具包：创建 Metaphor 客户端并返回搜索、获取内容、查找相似页面三个工具
    def build_toolkit(self) -> Tool:
        # 初始化 Metaphor API 客户端
        client = Metaphor(api_key=self.metaphor_api_key)

        # 使用搜索查询的工具：根据关键词搜索网页并返回结果
        @tool
        def search(query: str):
            """Call search engine with a query."""
            return client.search(query, use_autoprompt=self.use_autoprompt, num_results=self.search_num_results)

        # 获取网页内容的工具：根据搜索结果中的 ID 获取网页详细内容
        @tool
        def get_contents(ids: list[str]):
            """Get contents of a webpage.

            The ids passed in should be a list of ids as fetched from `search`.
            """
            return client.get_contents(ids)

        # 查找相似页面的工具：根据给定 URL 查找内容相似的网页
        @tool
        def find_similar(url: str):
            """Get search results similar to a given URL.

            The url passed in should be a URL returned from `search`
            """
            return client.find_similar(url, num_results=self.similar_num_results)

        # 返回包含三个工具的列表
        return [search, get_contents, find_similar]
