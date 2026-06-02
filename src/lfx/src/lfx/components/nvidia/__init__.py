from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

# 类型检查时的导入（仅用于静态类型检查，不会在运行时执行）
if TYPE_CHECKING:
    from .nvidia import NVIDIAModelComponent
    from .nvidia_embedding import NVIDIAEmbeddingsComponent
    from .nvidia_ingest import NvidiaIngestComponent
    from .nvidia_rerank import NvidiaRerankComponent

    # NvidiaSystemAssistComponent 仅在 Windows 平台可用
    if sys.platform == "win32":
        from .system_assist import NvidiaSystemAssistComponent

# 动态导入映射表：组件类名 -> 对应的模块名（不包含 .py 后缀）
_dynamic_imports = {
    "NVIDIAModelComponent": "nvidia",
    "NVIDIAEmbeddingsComponent": "nvidia_embedding",
    "NvidiaIngestComponent": "nvidia_ingest",
    "NvidiaRerankComponent": "nvidia_rerank",
}

# Windows 平台额外注册 SystemAssist 组件
if sys.platform == "win32":
    _dynamic_imports["NvidiaSystemAssistComponent"] = "system_assist"
    __all__ = [
        "NVIDIAEmbeddingsComponent",
        "NVIDIAModelComponent",
        "NvidiaIngestComponent",
        "NvidiaRerankComponent",
        "NvidiaSystemAssistComponent",
    ]
else:
    __all__ = [
        "NVIDIAEmbeddingsComponent",
        "NVIDIAModelComponent",
        "NvidiaIngestComponent",
        "NvidiaRerankComponent",
    ]


def __getattr__(attr_name: str) -> Any:
    """Lazily import nvidia components on attribute access."""
    # 当访问模块中未直接导入的属性时，触发懒加载导入
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过 import_mod 动态导入组件模块并获取对应类
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局字典中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 控制 dir() 的返回值，只暴露 __all__ 中声明的组件
    return list(__all__)
