# DuckDuckGo 搜索工具的 LangChain 集成
from langchain_community.tools import DuckDuckGoSearchRun

# 组件基类
from lfx.custom.custom_component.component import Component

# 输入组件类型
from lfx.inputs.inputs import IntInput, MessageTextInput

# 数据模型
from lfx.schema.data import Data

# 数据帧模型
from lfx.schema.dataframe import DataFrame

# 输出字段定义
from lfx.template.field.base import Output


# DuckDuckGo 搜索组件，用于执行网页搜索
class DuckDuckGoSearchComponent(Component):
    """Component for performing web searches using DuckDuckGo."""

    display_name = "DuckDuckGo Search"
    description = "Search the web using DuckDuckGo with customizable result limits"
    documentation = "https://python.langchain.com/docs/integrations/tools/ddg"
    icon = "DuckDuckGo"

    # 输入参数定义
    inputs = [
        # 搜索查询关键词
        MessageTextInput(
            name="input_value",
            display_name="Search Query",
            required=True,
            info="The search query to execute with DuckDuckGo",
            tool_mode=True,
        ),
        # 最大返回结果数量
        IntInput(
            name="max_results",
            display_name="Max Results",
            value=5,
            required=False,
            advanced=True,
            info="Maximum number of search results to return",
        ),
        # 每个结果片段的最大长度
        IntInput(
            name="max_snippet_length",
            display_name="Max Snippet Length",
            value=100,
            required=False,
            advanced=True,
            info="Maximum length of each result snippet",
        ),
    ]

    # 输出参数定义：返回表格格式的搜索结果
    outputs = [
        Output(display_name="Table", name="dataframe", method="fetch_content_dataframe"),
    ]

    # 构建 DuckDuckGo 搜索包装器实例
    def _build_wrapper(self) -> DuckDuckGoSearchRun:
        """Build the DuckDuckGo search wrapper."""
        return DuckDuckGoSearchRun()

    # 运行模型：执行搜索并返回 DataFrame 格式结果
    def run_model(self) -> DataFrame:
        return self.fetch_content_dataframe()

    # 执行搜索并返回 Data 对象列表
    def fetch_content(self) -> list[Data]:
        """Execute the search and return results as Data objects."""
        try:
            wrapper = self._build_wrapper()

            # 执行搜索，添加 site:* 以搜索所有网站
            full_results = wrapper.run(f"{self.input_value} (site:*)")

            # 按换行符分割结果并限制数量
            result_list = full_results.split("\n")[: self.max_results]

            # 将搜索结果转换为 Data 对象
            data_results = []
            for result in result_list:
                if result.strip():
                    # 截取片段到指定长度
                    snippet = result[: self.max_snippet_length]
                    data_results.append(
                        Data(
                            text=snippet,
                            data={
                                "content": result,
                                "snippet": snippet,
                            },
                        )
                    )
        except (ValueError, AttributeError) as e:
            # 捕获异常并返回错误数据
            error_data = [Data(text=str(e), data={"error": str(e)})]
            self.status = error_data
            return error_data
        else:
            self.status = data_results
            return data_results

    # 将搜索结果转换为 DataFrame 格式
    def fetch_content_dataframe(self) -> DataFrame:
        """Convert the search results to a DataFrame.

        Returns:
            DataFrame: A DataFrame containing the search results.
        """
        data = self.fetch_content()
        return DataFrame(data)
