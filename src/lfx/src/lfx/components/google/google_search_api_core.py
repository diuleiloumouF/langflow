# Google Search API Core 组件
# 本模块提供基于 Google Custom Search API 的搜索组件，用于在 Langflow 中执行 Google 搜索。

from langchain_google_community import GoogleSearchAPIWrapper

from lfx.custom.custom_component.component import Component
from lfx.io import IntInput, MultilineInput, Output, SecretStrInput
from lfx.schema.dataframe import DataFrame


class GoogleSearchAPICore(Component):
    """Google 搜索 API 核心组件。

    通过 Google Custom Search JSON API 执行搜索，并将结果以 DataFrame 格式返回。
    需要提供有效的 Google API Key 和搜索引擎 ID (CSE ID)。
    """

    # 在画布上显示的组件名称
    display_name = "Google Search API"
    # 组件的简要描述
    description = "Call Google Search API and return results as a DataFrame."
    # 组件图标
    icon = "Google"

    # 组件输入参数定义
    inputs = [
        SecretStrInput(
            name="google_api_key",
            display_name="Google API Key",
            required=True,
        ),
        SecretStrInput(
            name="google_cse_id",
            display_name="Google CSE ID",
            required=True,
        ),
        # 搜索输入文本，支持多行，开启 tool_mode 后可作为 LLM 工具调用
        MultilineInput(
            name="input_value",
            display_name="Input",
            tool_mode=True,
        ),
        # 返回的搜索结果数量，默认为 4 条
        IntInput(
            name="k",
            display_name="Number of results",
            value=4,
            required=True,
        ),
    ]

    # 组件输出参数定义
    outputs = [
        Output(
            display_name="Results",
            name="results",
            type_=DataFrame,
            # 绑定到 search_google 方法
            method="search_google",
        ),
    ]

    def search_google(self) -> DataFrame:
        """Search Google using the provided query."""
        # 校验 Google API Key 是否有效
        if not self.google_api_key:
            return DataFrame([{"error": "Invalid Google API Key"}])

        # 校验 Google 自定义搜索引擎 ID 是否有效
        if not self.google_cse_id:
            return DataFrame([{"error": "Invalid Google CSE ID"}])

        try:
            # 创建 Google Search API 包装器并执行搜索
            wrapper = GoogleSearchAPIWrapper(
                google_api_key=self.google_api_key, google_cse_id=self.google_cse_id, k=self.k
            )
            # 调用搜索接口获取结果
            results = wrapper.results(query=self.input_value, num_results=self.k)
            return DataFrame(results)
        except (ValueError, KeyError) as e:
            # 配置参数无效时的异常处理
            return DataFrame([{"error": f"Invalid configuration: {e!s}"}])
        except ConnectionError as e:
            # 网络连接失败时的异常处理
            return DataFrame([{"error": f"Connection error: {e!s}"}])
        except RuntimeError as e:
            # 搜索过程中发生的运行时错误处理
            return DataFrame([{"error": f"Error occurred while searching: {e!s}"}])

    def build(self):
        """构建组件，返回搜索方法的引用供下游调用。"""
        return self.search_google
