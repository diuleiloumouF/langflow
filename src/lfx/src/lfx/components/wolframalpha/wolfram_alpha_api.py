# WolframAlpha API 组件，通过 WolframAlpha 计算知识引擎查询数学、科学等结构化数据
from langchain_community.utilities.wolfram_alpha import WolframAlphaAPIWrapper

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import MultilineInput, SecretStrInput
from lfx.io import Output
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame


# WolframAlpha API 组件，支持计算查询并可作为工具使用
class WolframAlphaAPIComponent(LCToolComponent):
    # 组件显示名称
    display_name = "WolframAlpha API"
    # 组件描述
    description = """Enables queries to WolframAlpha for computational data, facts, and calculations across various \
topics, delivering structured responses."""
    # 组件内部名称
    name = "WolframAlphaAPI"

    # 组件输出定义
    outputs = [
        Output(display_name="Table", name="dataframe", method="fetch_content_dataframe"),
    ]

    # 组件输入参数定义
    inputs = [
        # 输入查询内容
        MultilineInput(
            name="input_value", display_name="Input Query", info="Example query: 'What is the population of France?'"
        ),
        # WolframAlpha 应用 ID（必填）
        SecretStrInput(name="app_id", display_name="WolframAlpha App ID", required=True),
    ]

    # 组件图标
    icon = "WolframAlphaAPI"

    # 运行模型并返回 DataFrame 格式结果
    def run_model(self) -> DataFrame:
        return self.fetch_content_dataframe()

    # 构建 WolframAlpha 工具实例，可作为 LangChain 工具使用
    def build_tool(self) -> Tool:
        wrapper = self._build_wrapper()
        return Tool(name="wolfram_alpha_api", description="Answers mathematical questions.", func=wrapper.run)

    # 构建 WolframAlpha API 包装器实例
    def _build_wrapper(self) -> WolframAlphaAPIWrapper:
        return WolframAlphaAPIWrapper(wolfram_alpha_appid=self.app_id)

    # 获取 WolframAlpha 查询内容
    def fetch_content(self) -> list[Data]:
        wrapper = self._build_wrapper()
        result_str = wrapper.run(self.input_value)
        data = [Data(text=result_str)]
        self.status = data
        return data

    # 将查询结果转换为 DataFrame 格式
    def fetch_content_dataframe(self) -> DataFrame:
        """将 WolframAlpha 查询结果转换为 DataFrame。

        Convert the WolframAlpha results to a DataFrame.

        Returns:
            DataFrame: A DataFrame containing the query results.
        """
        data = self.fetch_content()
        return DataFrame(data)
