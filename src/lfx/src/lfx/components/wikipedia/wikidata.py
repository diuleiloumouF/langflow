# Wikidata 查询组件，通过 Wikidata API 搜索知识图谱中的实体信息
import httpx
from httpx import HTTPError
from langchain_core.tools import ToolException

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import MultilineInput
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.template.field.base import Output


# Wikidata 查询组件，调用 Wikidata API 搜索实体并返回结构化数据
class WikidataComponent(Component):
    # 组件显示名称
    display_name = "Wikidata"
    # 组件描述
    description = "Performs a search using the Wikidata API."
    # 组件图标（复用 Wikipedia 图标）
    icon = "Wikipedia"

    # 组件输入参数定义
    inputs = [
        # 搜索查询文本
        MultilineInput(
            name="query",
            display_name="Query",
            info="The text query for similarity search on Wikidata.",
            required=True,
            tool_mode=True,
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(display_name="Table", name="dataframe", method="fetch_content_dataframe"),
    ]

    # 运行模型并返回 DataFrame 格式结果
    def run_model(self) -> DataFrame:
        return self.fetch_content_dataframe()

    # 获取 Wikidata 搜索内容
    def fetch_content(self) -> list[Data]:
        try:
            # Define request parameters for Wikidata API
            # 定义 Wikidata API 请求参数
            params = {
                "action": "wbsearchentities",
                "format": "json",
                "search": self.query,
                "language": "en",
            }

            # Send request to Wikidata API
            # 向 Wikidata API 发送搜索请求
            wikidata_api_url = "https://www.wikidata.org/w/api.php"
            response = httpx.get(wikidata_api_url, params=params)
            response.raise_for_status()
            response_json = response.json()

            # Extract search results
            # 提取搜索结果
            results = response_json.get("search", [])

            if not results:
                return [Data(data={"error": "No search results found for the given query."})]

            # Transform the API response into Data objects
            # 将 API 响应转换为 Data 对象列表
            data = [
                Data(
                    text=f"{result['label']}: {result.get('description', '')}",
                    data={
                        "label": result["label"],
                        "id": result.get("id"),
                        "url": result.get("url"),
                        "description": result.get("description", ""),
                        "concepturi": result.get("concepturi"),
                    },
                )
                for result in results
            ]

            self.status = data
        except HTTPError as e:
            error_message = f"HTTP Error in Wikidata Search API: {e!s}"
            raise ToolException(error_message) from None
        except KeyError as e:
            error_message = f"Data parsing error in Wikidata API response: {e!s}"
            raise ToolException(error_message) from None
        except ValueError as e:
            error_message = f"Value error in Wikidata API: {e!s}"
            raise ToolException(error_message) from None
        else:
            return data

    # 将搜索内容转换为 DataFrame 格式
    def fetch_content_dataframe(self) -> DataFrame:
        data = self.fetch_content()
        return DataFrame(data)
