"""Langflow backwards compatibility layer.

This module provides backwards compatibility by forwarding imports from
langflow.* to lfx.* to maintain compatibility with existing code that
references the old langflow module structure.
"""

# Langflow 向后兼容层
# 该模块通过将 langflow.* 的导入转发到 lfx.* 来提供向后兼容性
# 确保引用旧 langflow 模块结构的现有代码能够继续正常工作

from langflow.helpers.windows_postgres_helper import configure_windows_postgres_event_loop

# 配置 Windows 上的 PostgreSQL 事件循环策略
configure_windows_postgres_event_loop(source="package_init")

import importlib  # noqa: E402
import importlib.util  # noqa: E402
import sys  # noqa: E402
from types import ModuleType  # noqa: E402
from typing import Any  # noqa: E402


class LangflowCompatibilityModule(ModuleType):
    """A module that forwards attribute access to the corresponding lfx module."""

    # 兼容性模块类，将属性访问转发到对应的 lfx 模块

    def __init__(self, name: str, lfx_module_name: str):
        super().__init__(name)
        self._lfx_module_name = lfx_module_name  # 目标 lfx 模块名称
        self._lfx_module = None  # 缓存的 lfx 模块实例

    def _get_lfx_module(self):
        """Lazily import and cache the lfx module."""
        # 延迟导入并缓存 lfx 模块
        if self._lfx_module is None:
            try:
                self._lfx_module = importlib.import_module(self._lfx_module_name)
            except ImportError as e:
                msg = f"Cannot import {self._lfx_module_name} for backwards compatibility with {self.__name__}"
                raise ImportError(msg) from e
        return self._lfx_module

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the lfx module with caching."""
        # 将属性访问转发到 lfx 模块，并缓存结果以加速后续访问
        lfx_module = self._get_lfx_module()
        try:
            attr = getattr(lfx_module, name)
        except AttributeError as e:
            msg = f"module '{self.__name__}' has no attribute '{name}'"
            raise AttributeError(msg) from e
        else:
            # 将属性缓存到 __dict__ 中以加速后续访问
            setattr(self, name, attr)
            return attr

    def __dir__(self):
        """Return directory of the lfx module."""
        # 返回 lfx 模块的目录内容
        try:
            lfx_module = self._get_lfx_module()
            return dir(lfx_module)
        except ImportError:
            return []


def _setup_compatibility_modules():
    """Set up comprehensive compatibility modules for langflow.base imports."""
    # 设置 langflow.base 导入的全面兼容性模块
    # 首先，在当前模块（langflow）上设置 base 属性
    current_module = sys.modules[__name__]

    # 定义所有需要支持的模块映射关系
    module_mappings = {
        # 核心基础模块
        "langflow.base": "lfx.base",
        # 输入模块 - 对类标识至关重要
        "langflow.inputs": "lfx.inputs",
        "langflow.inputs.inputs": "lfx.inputs.inputs",
        # 模式模块 - 对类标识同样至关重要
        "langflow.schema": "lfx.schema",
        "langflow.schema.data": "lfx.schema.data",
        "langflow.schema.serialize": "lfx.schema.serialize",
        # 模板模块
        "langflow.template": "lfx.template",
        "langflow.template.field": "lfx.template.field",
        "langflow.template.field.base": "lfx.template.field.base",
        # 组件模块
        "langflow.components": "lfx.components",
        "langflow.components.helpers": "lfx.components.helpers",
        "langflow.components.helpers.calculator_core": "lfx.components.helpers.calculator_core",
        "langflow.components.helpers.create_list": "lfx.components.helpers.create_list",
        "langflow.components.helpers.current_date": "lfx.components.helpers.current_date",
        "langflow.components.helpers.id_generator": "lfx.components.helpers.id_generator",
        "langflow.components.helpers.memory": "lfx.components.helpers.memory",
        "langflow.components.helpers.output_parser": "lfx.components.helpers.output_parser",
        "langflow.components.helpers.store_message": "lfx.components.helpers.store_message",
        # lfx 中存在的独立模块
        "langflow.base.agents": "lfx.base.agents",
        "langflow.base.chains": "lfx.base.chains",
        "langflow.base.data": "lfx.base.data",
        "langflow.base.data.utils": "lfx.base.data.utils",
        "langflow.base.document_transformers": "lfx.base.document_transformers",
        "langflow.base.embeddings": "lfx.base.embeddings",
        "langflow.base.flow_processing": "lfx.base.flow_processing",
        "langflow.base.io": "lfx.base.io",
        "langflow.base.io.chat": "lfx.base.io.chat",
        "langflow.base.io.text": "lfx.base.io.text",
        "langflow.base.langchain_utilities": "lfx.base.langchain_utilities",
        "langflow.base.memory": "lfx.base.memory",
        "langflow.base.models": "lfx.base.models",
        "langflow.base.models.google_generative_ai_constants": "lfx.base.models.google_generative_ai_constants",
        "langflow.base.models.openai_constants": "lfx.base.models.openai_constants",
        "langflow.base.models.anthropic_constants": "lfx.base.models.anthropic_constants",
        "langflow.base.models.aiml_constants": "lfx.base.models.aiml_constants",
        "langflow.base.models.aws_constants": "lfx.base.models.aws_constants",
        "langflow.base.models.groq_constants": "lfx.base.models.groq_constants",
        "langflow.base.models.novita_constants": "lfx.base.models.novita_constants",
        "langflow.base.models.ollama_constants": "lfx.base.models.ollama_constants",
        "langflow.base.models.sambanova_constants": "lfx.base.models.sambanova_constants",
        "langflow.base.models.cometapi_constants": "lfx.base.models.cometapi_constants",
        "langflow.base.prompts": "lfx.base.prompts",
        "langflow.base.prompts.api_utils": "lfx.base.prompts.api_utils",
        "langflow.base.prompts.utils": "lfx.base.prompts.utils",
        "langflow.base.textsplitters": "lfx.base.textsplitters",
        "langflow.base.tools": "lfx.base.tools",
        "langflow.base.vectorstores": "lfx.base.vectorstores",
    }

    # 为每个映射创建兼容性模块
    for langflow_name, lfx_name in module_mappings.items():
        if langflow_name not in sys.modules:
            # 检查 lfx 模块是否存在
            try:
                spec = importlib.util.find_spec(lfx_name)
                if spec is not None:
                    # 创建兼容性模块
                    compat_module = LangflowCompatibilityModule(langflow_name, lfx_name)
                    sys.modules[langflow_name] = compat_module

                    # 设置模块层次结构
                    parts = langflow_name.split(".")
                    if len(parts) > 1:
                        parent_name = ".".join(parts[:-1])
                        parent_module = sys.modules.get(parent_name)
                        if parent_module is not None:
                            setattr(parent_module, parts[-1], compat_module)

                    # 顶层模块的特殊处理
                    if langflow_name == "langflow.base":
                        current_module.base = compat_module
                    elif langflow_name == "langflow.inputs":
                        current_module.inputs = compat_module
                    elif langflow_name == "langflow.schema":
                        current_module.schema = compat_module
                    elif langflow_name == "langflow.template":
                        current_module.template = compat_module
                    elif langflow_name == "langflow.components":
                        current_module.components = compat_module
            except (ImportError, ValueError):
                # 跳过 lfx 中不存在的模块
                continue

    # 处理仅存在于 langflow 中的模块（如 knowledge_bases）
    # 这些模块需要特殊处理，因为它们尚未迁移到 lfx
    langflow_only_modules = {
        "langflow.base.data.kb_utils": "langflow.base.data.kb_utils",
        "langflow.base.knowledge_bases": "langflow.base.knowledge_bases",
        "langflow.components.knowledge_bases": "langflow.components.knowledge_bases",
    }

    for langflow_name in langflow_only_modules:
        if langflow_name not in sys.modules:
            try:
                # 尝试找到实际的物理模块文件
                from pathlib import Path

                base_dir = Path(__file__).parent

                if langflow_name == "langflow.base.data.kb_utils":
                    kb_utils_file = base_dir / "base" / "data" / "kb_utils.py"
                    if kb_utils_file.exists():
                        spec = importlib.util.spec_from_file_location(langflow_name, kb_utils_file)
                        if spec is not None and spec.loader is not None:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[langflow_name] = module
                            spec.loader.exec_module(module)

                            # 同时添加到父模块
                            parent_module = sys.modules.get("langflow.base.data")
                            if parent_module is not None:
                                parent_module.kb_utils = module

                elif langflow_name == "langflow.base.knowledge_bases":
                    kb_dir = base_dir / "base" / "knowledge_bases"
                    kb_init_file = kb_dir / "__init__.py"
                    if kb_init_file.exists():
                        spec = importlib.util.spec_from_file_location(langflow_name, kb_init_file)
                        if spec is not None and spec.loader is not None:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[langflow_name] = module
                            spec.loader.exec_module(module)

                            # 同时添加到父模块
                            parent_module = sys.modules.get("langflow.base")
                            if parent_module is not None:
                                parent_module.knowledge_bases = module

                elif langflow_name == "langflow.components.knowledge_bases":
                    components_kb_dir = base_dir / "components" / "knowledge_bases"
                    components_kb_init_file = components_kb_dir / "__init__.py"
                    if components_kb_init_file.exists():
                        spec = importlib.util.spec_from_file_location(langflow_name, components_kb_init_file)
                        if spec is not None and spec.loader is not None:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[langflow_name] = module
                            spec.loader.exec_module(module)

                            # 同时添加到父模块
                            parent_module = sys.modules.get("langflow.components")
                            if parent_module is not None:
                                parent_module.knowledge_bases = module
            except (ImportError, AttributeError):
                # 如果直接文件加载失败，静默跳过
                continue


# 设置所有兼容性模块
_setup_compatibility_modules()
