from __future__ import annotations

# TYPE_CHECKING 用于类型检查时的导入，运行时不导入，避免循环依赖和性能问题
from typing import TYPE_CHECKING, Any

# 从导入工具模块导入动态导入函数
from lfx.components._importing import import_mod

# 仅在类型检查时导入具体组件类，运行时使用动态导入机制
if TYPE_CHECKING:
    from lfx.components.data_source.api_request import APIRequestComponent
    from lfx.components.data_source.csv_to_data import CSVToDataComponent
    from lfx.components.data_source.json_to_data import JSONToDataComponent
    from lfx.components.data_source.mock_data import MockDataGeneratorComponent
    from lfx.components.data_source.news_search import NewsSearchComponent
    from lfx.components.data_source.rss import RSSReaderComponent
    from lfx.components.data_source.sql_executor import SQLComponent
    from lfx.components.data_source.url import URLComponent
    from lfx.components.data_source.web_search import WebSearchComponent

# 动态导入映射表：组件类名 -> 所在模块名
# 用于延迟加载，只有在实际访问组件时才导入对应模块
_dynamic_imports = {
    "APIRequestComponent": "api_request",  # API 请求组件
    "CSVToDataComponent": "csv_to_data",  # CSV 转数据组件
    "JSONToDataComponent": "json_to_data",  # JSON 转数据组件
    "MockDataGeneratorComponent": "mock_data",  # 模拟数据生成器组件
    "NewsSearchComponent": "news_search",  # 新闻搜索组件
    "RSSReaderComponent": "rss",  # RSS 阅读器组件
    "URLComponent": "url",  # URL 组件
    "WebSearchComponent": "web_search",  # 网页搜索组件
    "SQLComponent": "sql_executor",  # SQL 执行器组件
}

# 模块公开导出的组件列表
__all__ = [
    "APIRequestComponent",
    "CSVToDataComponent",
    "JSONToDataComponent",
    "MockDataGeneratorComponent",
    "NewsSearchComponent",
    "RSSReaderComponent",
    "SQLComponent",
    "URLComponent",
    "WebSearchComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import data source components on attribute access."""
    # 当访问模块属性时，检查是否为已注册的动态导入组件
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 动态导入组件：根据类名和模块名查找并导入对应的组件类
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到模块全局命名空间中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    """自定义 dir() 返回值，只暴露 __all__ 中声明的组件名称"""
    return list(__all__)
