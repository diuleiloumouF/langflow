"""Processing components for LangFlow."""
# LangFlow 处理组件模块，提供文本处理、数据操作等功能的组件集合

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    # 以下为类型检查时的导入声明，用于静态类型检查工具（如 mypy）提供类型提示
    from lfx.components.processing.combine_text import CombineTextComponent
    from lfx.components.processing.converter import TypeConverterComponent
    from lfx.components.processing.create_list import CreateListComponent
    from lfx.components.processing.data_operations import DataOperationsComponent
    from lfx.components.processing.dataframe_operations import DataFrameOperationsComponent
    from lfx.components.processing.json_cleaner import JSONCleaner
    from lfx.components.processing.output_parser import OutputParserComponent
    from lfx.components.processing.parse_data import ParseDataComponent
    from lfx.components.processing.parser import ParserComponent
    from lfx.components.processing.regex import RegexExtractorComponent
    from lfx.components.processing.split_text import SplitTextComponent
    from lfx.components.processing.store_message import MessageStoreComponent

# 动态导入映射表：将组件类名映射到对应的子模块名，实现按需延迟加载
_dynamic_imports = {
    # CombineTextComponent: 文本合并组件，将多个文本片段合并为一个
    "CombineTextComponent": "combine_text",
    # TypeConverterComponent: 类型转换组件，将数据从一种类型转换为另一种类型
    "TypeConverterComponent": "converter",
    # CreateListComponent: 创建列表组件，将输入数据构造为列表
    "CreateListComponent": "create_list",
    # DataOperationsComponent: 数据操作组件，提供通用的数据处理操作
    "DataOperationsComponent": "data_operations",
    # DataFrameOperationsComponent: DataFrame 操作组件，对表格数据进行处理
    "DataFrameOperationsComponent": "dataframe_operations",
    # JSONCleaner: JSON 清洗组件，清理和规范化 JSON 数据
    "JSONCleaner": "json_cleaner",
    # OutputParserComponent: 输出解析组件，解析和提取模型输出中的结构化内容
    "OutputParserComponent": "output_parser",
    # ParseDataComponent: 数据解析组件，将原始数据解析为结构化格式
    "ParseDataComponent": "parse_data",
    # ParserComponent: 解析器组件，通用的数据解析功能
    "ParserComponent": "parser",
    # RegexExtractorComponent: 正则表达式提取组件，使用正则表达式从文本中提取匹配内容
    "RegexExtractorComponent": "regex",
    # SplitTextComponent: 文本分割组件，将长文本按规则拆分为多个片段
    "SplitTextComponent": "split_text",
    # MessageStoreComponent: 消息存储组件，存储和管理对话消息
    "MessageStoreComponent": "store_message",
}

# 模块公开接口列表，定义了 from lfx.components.processing import * 时可导出的组件
__all__ = [
    "CombineTextComponent",
    "CreateListComponent",
    "DataFrameOperationsComponent",
    "DataOperationsComponent",
    "JSONCleaner",
    "MessageStoreComponent",
    "OutputParserComponent",
    "ParseDataComponent",
    "ParserComponent",
    "RegexExtractorComponent",
    "SplitTextComponent",
    "TypeConverterComponent",
]


# 模块级延迟加载机制：通过自定义 __getattr__ 实现按需导入组件
# 当访问模块属性时（如 from lfx.components.processing import XXX），
# 才会实际导入对应的组件模块，避免模块加载时导入所有组件带来的性能开销
def __getattr__(attr_name: str) -> Any:
    """Lazily import processing components on attribute access."""
    # 检查请求的属性名是否在动态导入映射表中
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    globals()[attr_name] = result
    return result


# 自定义 dir() 输出，使 dir(module) 仅返回 __all__ 中声明的组件名称
def __dir__() -> list[str]:
    return list(__all__)
