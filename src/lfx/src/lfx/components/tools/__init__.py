# 工具组件模块的初始化文件
# Tools 模块提供各种工具类组件，用于在 Langflow 流程中执行特定功能（如计算、搜索、代码执行等）
# 采用延迟导入机制，只在实际使用时才加载对应的组件模块，减少启动时间

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from langchain_core._api.deprecation import LangChainDeprecationWarning

# 导入动态导入辅助函数
from lfx.components._importing import import_mod

# 类型检查时的导入（仅用于静态类型检查，运行时不会执行）
if TYPE_CHECKING:
    # 计算器工具组件
    from .calculator import CalculatorToolComponent

    # Python 代码结构化工具
    from .python_code_structured_tool import PythonCodeStructuredTool

    # Python REPL 工具组件
    from .python_repl import PythonREPLToolComponent

    # 搜索 API 组件
    from .search_api import SearchAPIComponent

    # SearXNG 搜索工具组件
    from .searxng import SearXNGToolComponent

    # SerpAPI 搜索组件
    from .serp_api import SerpAPIComponent

    # Tavily 搜索工具组件
    from .tavily_search_tool import TavilySearchToolComponent

    # Wikidata API 组件
    from .wikidata_api import WikidataAPIComponent

    # Wikipedia API 组件
    from .wikipedia_api import WikipediaAPIComponent

    # Yahoo Finance 工具组件
    from .yahoo_finance import YfinanceToolComponent

# 动态导入映射表：组件名称 -> 模块名称
# 用于延迟导入机制，当访问某个组件时，通过此映射找到对应的模块并导入
_dynamic_imports = {
    "CalculatorToolComponent": "calculator",
    "PythonCodeStructuredTool": "python_code_structured_tool",
    "PythonREPLToolComponent": "python_repl",
    "SearchAPIComponent": "search_api",
    "SearXNGToolComponent": "searxng",
    "SerpAPIComponent": "serp_api",
    "TavilySearchToolComponent": "tavily_search_tool",
    "WikidataAPIComponent": "wikidata_api",
    "WikipediaAPIComponent": "wikipedia_api",
    "YfinanceToolComponent": "yahoo_finance",
}

# 模块公开导出的组件列表，定义 `from lfx.components.tools import *` 时导出的内容
__all__ = [
    "CalculatorToolComponent",
    "PythonCodeStructuredTool",
    "PythonREPLToolComponent",
    "SearXNGToolComponent",
    "SearchAPIComponent",
    "SerpAPIComponent",
    "TavilySearchToolComponent",
    "WikidataAPIComponent",
    "WikipediaAPIComponent",
    "YfinanceToolComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import tool components on attribute access."""
    # 当访问模块中不存在的属性时，通过动态导入机制加载对应的组件
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 忽略 LangChain 的弃用警告，避免在导入时产生不必要的警告信息
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", LangChainDeprecationWarning)
            # 调用 import_mod 执行动态导入，从对应的子模块中加载组件类
            result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入的组件缓存到全局命名空间中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    """自定义 dir() 函数的返回值，确保 `dir(tools)` 只返回公开导出的组件名称"""
    return list(__all__)
