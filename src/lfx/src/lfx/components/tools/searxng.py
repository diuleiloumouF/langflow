import json
from collections.abc import Sequence
from typing import Any

import requests
from langchain_classic.agents import Tool
from langchain_core.tools import StructuredTool
from pydantic.v1 import Field, create_model

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.inputs.inputs import DropdownInput, IntInput, MessageTextInput, MultiselectInput
from lfx.io import Output
from lfx.log.logger import logger
from lfx.schema.dotdict import dotdict


class SearXNGToolComponent(LCToolComponent):
    """SearXNG 搜索组件，基于 SearXNG 元搜索引擎提供搜索工具。

    该组件允许用户通过配置 SearXNG 实例的 URL、搜索类别、语言等参数，
    动态构建一个可被 LangChain Agent 调用的搜索工具。
    """

    # 自定义 HTTP 请求头，用于向 SearXNG 发送请求
    search_headers: dict = {}
    # 组件在画布上显示的名称
    display_name = "SearXNG Search"
    # 组件描述信息
    description = "A component that searches for tools using SearXNG."
    # 组件内部标识名
    name = "SearXNGTool"
    # 标记为遗留组件，不再作为新组件推荐使用
    legacy: bool = True

    # 组件输入参数定义
    inputs = [
        # SearXNG 实例的 URL 地址，支持刷新按钮以自动获取可用类别和语言
        MessageTextInput(
            name="url",
            display_name="URL",
            value="http://localhost",
            required=True,
            refresh_button=True,
        ),
        # 最大返回结果数量
        IntInput(
            name="max_results",
            display_name="Max Results",
            value=10,
            required=True,
        ),
        # 搜索类别多选，选项从 SearXNG 实例动态获取
        MultiselectInput(
            name="categories",
            display_name="Categories",
            options=[],
            value=[],
        ),
        # 搜索语言下拉选择，选项从 SearXNG 实例动态获取
        DropdownInput(
            name="language",
            display_name="Language",
            options=[],
        ),
    ]

    # 组件输出定义：构建并返回一个搜索工具
    outputs = [
        Output(display_name="Tool", name="result_tool", method="build_tool"),
    ]

    def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None) -> dotdict:
        """当用户修改输入字段时，动态更新构建配置。

        主要逻辑：当 URL 字段发生变化时，请求 SearXNG 的 /config 接口，
        获取可用的搜索类别和语言列表，更新到构建配置中。

        Args:
            build_config: 当前的构建配置字典。
            field_value: 被修改字段的新值。
            field_name: 被修改的字段名称。

        Returns:
            更新后的构建配置。
        """
        if field_name is None:
            return build_config

        # 只有当 URL 字段发生变化时才触发更新
        if field_name != "url":
            return build_config

        try:
            url = f"{field_value}/config"

            # 请求 SearXNG 的配置接口，获取可用类别和语言
            response = requests.get(url=url, headers=self.search_headers.copy(), timeout=10)
            data = None
            # 处理 zstd 压缩的响应体
            if response.headers.get("Content-Encoding") == "zstd":
                data = json.loads(response.content)
            else:
                data = response.json()
            # 更新搜索类别选项，同时清理已选但不再可用的类别
            build_config["categories"]["options"] = data["categories"].copy()
            for selected_category in build_config["categories"]["value"]:
                if selected_category not in build_config["categories"]["options"]:
                    build_config["categories"]["value"].remove(selected_category)
            # 更新语言选项
            languages = list(data["locales"])
            build_config["language"]["options"] = languages.copy()
        except Exception as e:  # noqa: BLE001
            # 配置获取失败时，将错误信息显示在状态中
            self.status = f"Failed to extract names: {e}"
            logger.debug(self.status, exc_info=True)
            build_config["categories"]["options"] = ["Failed to parse", str(e)]
        return build_config

    def build_tool(self) -> Tool:
        """构建并返回一个 SearXNG 搜索工具实例。

        在内部定义一个 SearxSearch 辅助类，将组件的配置参数（URL、类别、语言等）
        注入其中，然后通过 LangChain 的 StructuredTool.from_function 方法
        将其包装为一个带有参数 Schema 的标准化工具。

        Returns:
            一个可被 LangChain Agent 调用的 StructuredTool 实例。
        """

        class SearxSearch:
            """SearXNG 搜索的内部辅助类，封装搜索逻辑。"""

            _url: str = ""
            _categories: list[str] = []
            _language: str = ""
            _headers: dict = {}
            _max_results: int = 10

            @staticmethod
            def search(query: str, categories: Sequence[str] = ()) -> list:
                """执行 SearXNG 搜索。

                Args:
                    query: 搜索关键词。
                    categories: 附加搜索类别，会与默认类别合并。

                Returns:
                    搜索结果列表，每项为一个字典。

                Raises:
                    ValueError: 当没有提供任何搜索类别时抛出。
                """
                if not SearxSearch._categories and not categories:
                    msg = "No categories provided."
                    raise ValueError(msg)
                # 合并默认类别和临时类别，去重
                all_categories = SearxSearch._categories + list(set(categories) - set(SearxSearch._categories))
                try:
                    url = f"{SearxSearch._url}/"
                    headers = SearxSearch._headers.copy()
                    # 发送搜索请求到 SearXNG 实例
                    response = requests.get(
                        url=url,
                        headers=headers,
                        params={
                            "q": query,
                            "categories": ",".join(all_categories),
                            "language": SearxSearch._language,
                            "format": "json",
                        },
                        timeout=10,
                    ).json()

                    # 根据最大结果数限制返回数量
                    num_results = min(SearxSearch._max_results, len(response["results"]))
                    return [response["results"][i] for i in range(num_results)]
                except Exception as e:  # noqa: BLE001
                    logger.debug("Error running SearXNG Search", exc_info=True)
                    return [f"Failed to search: {e}"]

        # 将组件实例的配置注入到 SearxSearch 类变量中
        SearxSearch._url = self.url
        SearxSearch._categories = self.categories.copy()
        SearxSearch._language = self.language
        SearxSearch._headers = self.search_headers.copy()
        SearxSearch._max_results = self.max_results

        # 将 SearxSearch 注入全局作用域，以便 LangChain 反序列化时能找到该类
        globals_ = globals()
        local = {}
        local["SearxSearch"] = SearxSearch
        globals_.update(local)

        # 动态构建工具的参数 Schema，定义 query 和 categories 两个参数
        schema_fields = {
            "query": (str, Field(..., description="The query to search for.")),
            "categories": (
                list[str],
                Field(default=[], description="The categories to search in."),
            ),
        }

        searx_search_schema = create_model("SearxSearchSchema", **schema_fields)

        # 将搜索函数包装为 StructuredTool，供 Agent 调用
        return StructuredTool.from_function(
            func=local["SearxSearch"].search,
            args_schema=searx_search_schema,
            name="searxng_search_tool",
            description="A tool that searches for tools using SearXNG.\nThe available categories are: "
            + ", ".join(self.categories),
        )
