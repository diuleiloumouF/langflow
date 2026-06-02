from lfx.custom.custom_component.component import Component
from lfx.io import (
    MessageTextInput,
    Output,
    SecretStrInput,
)
from lfx.schema.data import Data


# ScrapeGraph 搜索 API 组件
# 通过 ScrapeGraph 的搜索服务，根据用户提供的搜索提示词返回搜索结果
class ScrapeGraphSearchApi(Component):
    # 组件在画布上的显示名称
    display_name: str = "ScrapeGraph Search API"
    # 组件描述信息
    description: str = "Given a search prompt, it will return search results using ScrapeGraph's search functionality."
    # 组件内部名称，用于流程 JSON 序列化
    name = "ScrapeGraphSearchApi"

    # ScrapeGraph 官方文档链接
    documentation: str = "https://docs.scrapegraphai.com/services/searchscraper"
    # 组件图标
    icon = "ScrapeGraph"

    # 组件输入参数定义
    inputs = [
        # ScrapeGraph API 密钥，用于身份认证
        SecretStrInput(
            name="api_key",
            display_name="ScrapeGraph API Key",
            required=True,
            password=True,
            info="The API key to use ScrapeGraph API.",
        ),
        # 搜索提示词，用户输入的搜索关键词或描述
        MessageTextInput(
            name="user_prompt",
            display_name="Search Prompt",
            tool_mode=True,
            info="The search prompt to use.",
        ),
    ]

    # 组件输出参数定义，调用 search 方法返回 JSON 数据
    outputs = [
        Output(display_name="JSON", name="data", method="search"),
    ]

    # 执行搜索操作，调用 ScrapeGraph SearchScraper 服务并返回结果
    def search(self) -> list[Data]:
        # 延迟导入 scrapegraph-py 依赖，避免硬依赖
        try:
            from scrapegraph_py import Client
            from scrapegraph_py.logger import sgai_logger
        except ImportError as e:
            msg = "Could not import scrapegraph-py package. Please install it with `pip install scrapegraph-py`."
            raise ImportError(msg) from e

        # Set logging level
        sgai_logger.set_logging(level="INFO")

        # Initialize the client with API key
        sgai_client = Client(api_key=self.api_key)

        try:
            # SearchScraper request
            response = sgai_client.searchscraper(
                user_prompt=self.user_prompt,
            )

            # Close the client
            sgai_client.close()

            # 将搜索结果封装为 Data 对象返回
            return Data(data=response)
        except Exception:
            # 异常时确保关闭客户端连接，释放资源
            sgai_client.close()
            raise
