# 启用延迟注解求值，避免循环导入问题
from __future__ import annotations

# 类型检查相关导入，运行时不执行
from typing import TYPE_CHECKING, Any

# 动态导入工具函数
from lfx.components._importing import import_mod

# 云环境检测工具
from lfx.utils.validate_cloud import is_astra_cloud_environment

# 仅在类型检查时导入，避免运行时循环依赖
if TYPE_CHECKING:
    from .chunk_docling_document import ChunkDoclingDocumentComponent  # noqa: F401
    from .docling_inline import DoclingInlineComponent  # noqa: F401
    from .docling_remote import DoclingRemoteComponent  # noqa: F401
    from .export_docling_document import ExportDoclingDocumentComponent  # noqa: F401

# 所有组件列表
_all_components = [
    "ChunkDoclingDocumentComponent",
    "DoclingInlineComponent",
    "DoclingRemoteComponent",
    "ExportDoclingDocumentComponent",
]

# 所有动态导入映射表：组件类名 -> 所在模块名
_all_dynamic_imports = {
    "ChunkDoclingDocumentComponent": "chunk_docling_document",
    "DoclingInlineComponent": "docling_inline",
    "DoclingRemoteComponent": "docling_remote",
    "ExportDoclingDocumentComponent": "export_docling_document",
}

# 需要本地 Docling/EasyOCR 依赖的组件（在云环境中禁用）
_cloud_disabled_components = {
    "ChunkDoclingDocumentComponent",
    "DoclingInlineComponent",
    "ExportDoclingDocumentComponent",
}


# 获取可用组件列表，过滤掉云环境中禁用的组件
def _get_available_components() -> list[str]:
    """Get list of available components, filtering out cloud-disabled ones."""
    if is_astra_cloud_environment():
        # 在云环境中仅显示 DoclingRemoteComponent（Docling Serve）
        return [comp for comp in _all_components if comp not in _cloud_disabled_components]
    return _all_components


# 获取动态导入映射表，过滤掉云环境中禁用的组件
def _get_dynamic_imports() -> dict[str, str]:
    """Get dynamic imports dict, filtering out cloud-disabled ones."""
    if is_astra_cloud_environment():
        # 在云环境中仅允许使用 DoclingRemoteComponent（Docling Serve）
        return {k: v for k, v in _all_dynamic_imports.items() if k not in _cloud_disabled_components}
    return _all_dynamic_imports


# 根据云环境动态设置 __all__ 和 _dynamic_imports
__all__: list[str] = _get_available_components()  # noqa: PLE0605
_dynamic_imports: dict[str, str] = _get_dynamic_imports()


# 通过属性访问实现延迟导入，仅在实际使用时才加载组件模块
def __getattr__(attr_name: str) -> Any:
    """Lazily import docling components on attribute access."""
    # 检查组件是否可用（未在云环境中禁用）
    if is_astra_cloud_environment() and attr_name in _cloud_disabled_components:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)

    if attr_name not in _all_dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        result = import_mod(attr_name, _all_dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    globals()[attr_name] = result
    return result


# 限制 dir() 返回的属性列表，只包含可用的组件
def __dir__() -> list[str]:
    return _get_available_components()
