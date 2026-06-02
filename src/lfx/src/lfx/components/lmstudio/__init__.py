# LMStudio 组件包的初始化模块
# 提供 LMStudio 的嵌入模型组件和语言模型组件的延迟导入机制

from __future__ import annotations

from typing import TYPE_CHECKING, Any

# 动态导入工具函数，用于按需加载组件模块
from lfx.components._importing import import_mod

# 类型检查时的静态导入，用于 IDE 代码补全和类型推导
if TYPE_CHECKING:
    from lfx.components.lmstudio.lmstudioembeddings import LMStudioEmbeddingsComponent
    from lfx.components.lmstudio.lmstudiomodel import LMStudioModelComponent

# 动态导入映射表：组件类名 -> 模块名（不含 .py 后缀）
# 访问组件属性时，根据此映射按需导入对应模块
_dynamic_imports = {
    "LMStudioEmbeddingsComponent": "lmstudioembeddings",
    "LMStudioModelComponent": "lmstudiomodel",
}

# 模块的公开 API 列表，同时供 __dir__ 使用
__all__ = ["LMStudioEmbeddingsComponent", "LMStudioModelComponent"]


def __getattr__(attr_name: str) -> Any:
    """Lazily import lmstudio components on attribute access."""
    # 属性名不在映射表中时，抛出 AttributeError
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 调用 import_mod 动态加载对应的组件模块并获取组件类
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到模块的全局命名空间中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 控制 dir() 的输出，仅返回 __all__ 中声明的公开组件
    return list(__all__)
