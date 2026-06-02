# HTTP 请求库，用于调用 Tavily API
import httpx

# Langflow 组件基类
from lfx.custom import Component

# 输入/输出组件类型定义
from lfx.io import BoolInput, DropdownInput, MessageTextInput, Output, SecretStrInput

# 日志记录器
from lfx.log.logger import logger

# 数据模型
from lfx.schema import Data

# DataFrame 数据模型，用于表格输出
from lfx.schema.dataframe import DataFrame


class TavilyExtractComponent(Component):
    """Separate component specifically for Tavily Extract functionality."""

    # 组件显示名称
    display_name = "Tavily Extract API"
    description = """**Tavily Extract** extract raw content from URLs."""
    icon = "TavilyIcon"

    # 组件输入参数定义
    inputs = [
        # Tavily API 密钥，必填的敏感信息输入
        SecretStrInput(
            name="api_key",
            display_name="Tavily API Key",
            required=True,
            info="Your Tavily API Key.",
        ),
        # 要提取内容的 URL 列表，以逗号分隔
        MessageTextInput(
            name="urls",
            display_name="URLs",
            info="Comma-separated list of URLs to extract content from.",
            required=True,
        ),
        # 提取深度选项：basic（基础）或 advanced（高级），默认为 basic
        DropdownInput(
            name="extract_depth",
            display_name="Extract Depth",
            info="The depth of the extraction process.",
            options=["basic", "advanced"],
            value="basic",
            advanced=True,
        ),
        # 是否包含从 URL 中提取的图片列表，默认为 False
        BoolInput(
            name="include_images",
            display_name="Include Images",
            info="Include a list of images extracted from the URLs.",
            value=False,
            advanced=True,
        ),
    ]

    # 组件输出定义：将提取结果以 DataFrame 表格形式输出
    outputs = [
        Output(display_name="Table", name="dataframe", method="fetch_content"),
    ]

    def run_model(self) -> DataFrame:
        # 执行模型：调用 fetch_content_dataframe 获取内容并返回 DataFrame
        return self.fetch_content_dataframe()

    def fetch_content(self) -> list[Data]:
        """Fetches and processes extracted content into a list of Data objects."""
        try:
            # 按逗号分割 URL 并清理空白字符
            # Split URLs by comma and clean them
            urls = [url.strip() for url in (self.urls or "").split(",") if url.strip()]
            if not urls:
                error_message = "No valid URLs provided"
                logger.error(error_message)
                return [Data(text=error_message, data={"error": error_message})]

            # Tavily Extract API 的端点地址
            url = "https://api.tavily.com/extract"
            # HTTP 请求头，包含内容类型、接受格式和授权令牌
            headers = {
                "content-type": "application/json",
                "accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            # 请求负载：包含 URL 列表、提取深度和是否包含图片的参数
            payload = {
                "urls": urls,
                "extract_depth": self.extract_depth,
                "include_images": self.include_images,
            }

            # 使用 httpx 客户端发起 POST 请求，超时时间为 90 秒
            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()

        except httpx.TimeoutException as exc:
            # 请求超时异常处理（90秒超时）
            error_message = f"Request timed out (90s): {exc}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        except httpx.HTTPStatusError as exc:
            # HTTP 状态码错误异常处理
            error_message = f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        except (ValueError, KeyError, AttributeError, httpx.RequestError) as exc:
            # 数据处理相关异常处理
            error_message = f"Data processing error: {exc}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        else:
            # 请求成功，解析 JSON 响应
            extract_results = response.json()
            data_results = []

            # 处理成功提取的结果
            # Process successful extractions
            for result in extract_results.get("results", []):
                raw_content = result.get("raw_content", "")
                images = result.get("images", [])
                # 将每个提取结果封装为 Data 对象，raw_content 作为 text，其余信息作为 data
                result_data = {"url": result.get("url"), "raw_content": raw_content, "images": images}
                data_results.append(Data(text=raw_content, data=result_data))

            # 处理失败的提取结果，将失败信息作为单独的 Data 对象添加
            # Process failed extractions
            if extract_results.get("failed_results"):
                data_results.append(
                    Data(
                        text="Failed extractions",
                        data={"failed_results": extract_results["failed_results"]},
                    )
                )

            # 将提取结果保存到组件状态，供 UI 显示
            self.status = data_results
            return data_results

    def fetch_content_dataframe(self) -> DataFrame:
        # 获取提取内容并转换为 DataFrame 格式输出
        data = self.fetch_content()
        return DataFrame(data)
