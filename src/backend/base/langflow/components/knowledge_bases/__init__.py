"""Langflow knowledge bases module - forwards to lfx.components.files_and_knowledge.

This module provides backwards compatibility by forwarding all imports
to files_and_knowledge where the actual knowledge base components are located.
"""

# Langflow 知识库模块
# 将所有导入转发到 lfx.components.files_and_knowledge，提供向后兼容性
# 知识库组件的实际实现位于 files_and_knowledge 模块中

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import types

# 从 lfx.components.files_and_knowledge 导入公开 API 列表
from lfx.components.files_and_knowledge import __all__ as _lfx_all

__all__: list[str] = list(_lfx_all)

# 在 sys.modules 中注册重定向的子模块，以便 importlib.import_module() 直接调用
# 这允许使用类似 import langflow.components.knowledge_bases.ingestion 的导入方式
_redirected_submodules = {
    # "langflow.components.knowledge_bases.ingestion": "lfx.components.files_and_knowledge.ingestion",
    "langflow.components.knowledge_bases.retrieval": "lfx.components.files_and_knowledge.retrieval",
}

for old_path, new_path in _redirected_submodules.items():
    if old_path not in sys.modules:
        # 使用延迟加载器，在访问时才导入实际模块
        class _RedirectedModule:
            _module: types.ModuleType | None

            def __init__(self, target_path: str, original_path: str):
                self._target_path = target_path
                self._original_path = original_path
                self._module = None

            def __getattr__(self, name: str) -> Any:
                if self._module is None:
                    from importlib import import_module

                    self._module = import_module(self._target_path)
                    # 同时在原始路径下注册，以便后续导入使用
                    sys.modules[self._original_path] = self._module
                return getattr(self._module, name)

            def __repr__(self) -> str:
                return f"<redirected module '{self._original_path}' -> '{self._target_path}'>"

        sys.modules[old_path] = _RedirectedModule(new_path, old_path)  # type: ignore[assignment]


def __getattr__(attr_name: str) -> Any:
    """Forward attribute access to lfx.components.files_and_knowledge."""
    # 处理子模块访问以实现向后兼容
    if attr_name == "retrieval":
        from importlib import import_module

        result = import_module("lfx.components.files_and_knowledge.retrieval")
        globals()[attr_name] = result
        return result

    from lfx.components import files_and_knowledge

    return getattr(files_and_knowledge, attr_name)


def __dir__() -> list[str]:
    """Forward dir() to lfx.components.files_and_knowledge."""
    # 将 dir() 调用转发到 lfx.components.files_and_knowledge
    return list(__all__)
