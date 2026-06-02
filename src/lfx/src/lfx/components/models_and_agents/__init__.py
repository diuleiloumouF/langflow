# 启用延迟注释评估，允许在注释中使用前向引用
from __future__ import annotations

from typing import TYPE_CHECKING, Any

# 导入动态模块加载函数，用于按需加载组件
from lfx.components._importing import import_mod

# 仅在类型检查时导入组件类，避免运行时循环依赖
if TYPE_CHECKING:
    # 智能体组件：用于构建 AI 智能体
    from lfx.components.models_and_agents.agent import AgentComponent

    # 嵌入模型组件：用于文本向量化
    from lfx.components.models_and_agents.embedding_model import EmbeddingModelComponent

    # 语言模型组件：用于与 LLM 交互
    from lfx.components.models_and_agents.language_model import LanguageModelComponent

    # MCP 工具组件：用于访问 MCP 协议工具
    from lfx.components.models_and_agents.mcp_component import MCPToolsComponent

    # 记忆组件：用于管理对话历史和上下文
    from lfx.components.models_and_agents.memory import MemoryComponent

    # 策略组件：用于定义智能体行为策略
    from lfx.components.models_and_agents.policies_component import PoliciesComponent

    # 提示词组件：用于管理提示词模板
    from lfx.components.models_and_agents.prompt import PromptComponent

# 动态导入映射表：组件类名 -> 模块名
# 用于按需延迟加载组件，减少启动时间
_dynamic_imports = {
    "AgentComponent": "agent",
    "EmbeddingModelComponent": "embedding_model",
    "LanguageModelComponent": "language_model",
    "MCPToolsComponent": "mcp_component",
    "MemoryComponent": "memory",
    "PromptComponent": "prompt",
    "PoliciesComponent": "policies_component",
}

# 导出的公共组件列表
__all__ = [
    "AgentComponent",
    "EmbeddingModelComponent",
    "LanguageModelComponent",
    "MCPToolsComponent",
    "MemoryComponent",
    "PoliciesComponent",
    "PromptComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import model and agent components on attribute access.
    访问属性时延迟导入模型和智能体组件
    """
    # 检查请求的属性是否在动态导入映射中
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 使用 import_mod 函数动态加载组件模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        # 捕获导入错误并提供清晰的错误信息
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将加载的结果缓存到全局变量中，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 自定义 dir() 返回值，只显示导出的公共组件
    return list(__all__)
