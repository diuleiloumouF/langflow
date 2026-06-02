# 文件与知识库组件模块
# 提供目录操作、文件处理、知识库摄取和检索等功能组件

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 仅在类型检查时导入组件类，避免循环导入和性能开销
if TYPE_CHECKING:
    from lfx.components.files_and_knowledge.directory import DirectoryComponent
    from lfx.components.files_and_knowledge.file import FileComponent
    from lfx.components.files_and_knowledge.ingestion import KnowledgeIngestionComponent
    from lfx.components.files_and_knowledge.retrieval import KnowledgeBaseComponent
    from lfx.components.files_and_knowledge.save_file import SaveToFileComponent

# 动态导入映射表：组件名称 -> 子模块名称
# 用于实现按需导入，提升模块加载性能
_dynamic_imports = {
    "DirectoryComponent": "directory",
    "FileComponent": "file",
    "KnowledgeIngestionComponent": "ingestion",
    "KnowledgeBaseComponent": "retrieval",
    "SaveToFileComponent": "save_file",
}

# 模块公开接口，定义可导出的组件列表
__all__ = [
    "DirectoryComponent",
    "FileComponent",
    "KnowledgeBaseComponent",
    "KnowledgeIngestionComponent",
    "SaveToFileComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import files and knowledge components on attribute access."""
    # 属性访问时动态导入组件，避免一次性加载所有组件
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过 import_mod 函数按需加载指定组件模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 自定义 dir() 输出，只显示模块中实际可用的组件
    return list(__all__)
