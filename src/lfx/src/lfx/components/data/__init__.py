# 数据模块 - data_source 的向后兼容别名
#
# 本模块通过将所有导入转发到 data_source（实际数据组件所在的位置）来提供向后兼容性。
# 新代码应直接从 lfx.components.data_source 导入所需组件。
"""Data module - backwards compatibility alias for data_source.

This module provides backwards compatibility by forwarding all imports
to data_source where the actual data components are located.
"""

from __future__ import annotations

from typing import Any

from lfx.components._importing import import_mod

# 复制 data_source 中相同的动态导入映射，用于向后兼容
# 键为组件类名，值为目标模块名（或 (模块名, 包名) 元组）
_dynamic_imports = {
    "APIRequestComponent": "api_request",
    "CSVToDataComponent": "csv_to_data",
    "JSONToDataComponent": "json_to_data",
    "MockDataGeneratorComponent": "mock_data",
    "NewsSearchComponent": "news_search",
    "RSSReaderComponent": "rss",
    "URLComponent": "url",
    "WebSearchComponent": "web_search",
    # File and Directory components are in files_and_knowledge, forward them for backwards compatibility
    "FileComponent": ("file", "files_and_knowledge"),
    "DirectoryComponent": ("directory", "files_and_knowledge"),
}

# 模块的公开接口列表，定义了可以从本模块导出的所有组件
__all__ = [
    "APIRequestComponent",
    "CSVToDataComponent",
    "DirectoryComponent",
    "FileComponent",
    "JSONToDataComponent",
    "MockDataGeneratorComponent",
    "NewsSearchComponent",
    "RSSReaderComponent",
    "URLComponent",
    "WebSearchComponent",
]


# 以下为已迁移组件的子模块访问处理，用于向后兼容旧的导入路径


def __getattr__(attr_name: str) -> Any:
    """Forward attribute access to data_source components.

    将属性访问转发到 data_source 中的组件实现。
    """
    # 处理子模块访问的向后兼容
    # 例如：lfx.components.data.directory -> lfx.components.files_and_knowledge.directory
    if attr_name == "directory":
        from importlib import import_module

        result = import_module("lfx.components.files_and_knowledge.directory")
        globals()[attr_name] = result
        return result
    # FileComponent 已迁移至 files_and_knowledge 包
    if attr_name == "file":
        from importlib import import_module

        result = import_module("lfx.components.files_and_knowledge.file")
        globals()[attr_name] = result
        return result
    # 数据源组件已迁移至 data_source 包
    if attr_name == "news_search":
        from importlib import import_module

        result = import_module("lfx.components.data_source.news_search")
        globals()[attr_name] = result
        return result
    if attr_name == "rss":
        from importlib import import_module

        result = import_module("lfx.components.data_source.rss")
        globals()[attr_name] = result
        return result
    if attr_name == "web_search":
        from importlib import import_module

        result = import_module("lfx.components.data_source.web_search")
        globals()[attr_name] = result
        return result
    # SQLComponent 已迁移至 utilities 包
    if attr_name == "sql_executor":
        from importlib import import_module

        result = import_module("lfx.components.utilities.sql_executor")
        globals()[attr_name] = result
        return result

    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)

    mapping = _dynamic_imports[attr_name]

    # 处理 FileComponent 和 DirectoryComponent，它们位于 files_and_knowledge 包中
    if isinstance(mapping, tuple):
        module_name, package = mapping
        try:
            result = import_mod(attr_name, module_name, f"lfx.components.{package}")
        except (ModuleNotFoundError, ImportError, AttributeError) as e:
            msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
            raise AttributeError(msg) from e
    else:
        # 从 data_source 包导入，使用正确的包路径
        package = "lfx.components.data_source"
        try:
            result = import_mod(attr_name, mapping, package)
        except (ModuleNotFoundError, ImportError, AttributeError) as e:
            msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
            raise AttributeError(msg) from e

    # 将导入结果缓存到模块全局变量中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    """Return directory of available components.

    返回本模块中可用组件的目录列表。
    """
    return list(__all__)
