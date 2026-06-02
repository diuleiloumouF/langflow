# ScrapeGraph 组件包初始化模块
# 提供 ScrapeGraph 网页抓取相关组件的延迟加载机制

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# TYPE_CHECKING 块：仅在类型检查时导入，用于 IDE 补全和类型分析，避免运行时循环导入
if TYPE_CHECKING:
    from .scrapegraph_markdownify_api import ScrapeGraphMarkdownifyApi
    from .scrapegraph_search_api import ScrapeGraphSearchApi
    from .scrapegraph_smart_scraper_api import ScrapeGraphSmartScraperApi

# 动态导入映射表：组件类名 -> 模块文件名（不含 .py 后缀）
_dynamic_imports = {
    "ScrapeGraphMarkdownifyApi": "scrapegraph_markdownify_api",
    "ScrapeGraphSearchApi": "scrapegraph_search_api",
    "ScrapeGraphSmartScraperApi": "scrapegraph_smart_scraper_api",
}

# 公开导出的组件列表
__all__ = [
    "ScrapeGraphMarkdownifyApi",
    "ScrapeGraphSearchApi",
    "ScrapeGraphSmartScraperApi",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import scrapegraph components on attribute access."""
    # 当访问模块属性时，检查是否在动态导入映射中
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过 import_mod 执行延迟导入，避免模块加载时引入不必要的依赖
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到模块全局命名空间，后续访问不再重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 输出为公开导出的组件列表，保持模块接口整洁
    return list(__all__)
