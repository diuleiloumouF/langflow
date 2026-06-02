"""Langflow Agentic Flows.

Langflow 智能体流程模块，包含 Langflow 助手功能的流程定义。

This package contains flow definitions for the Langflow Assistant feature.

Available flows:
- translation_flow: Intent classification and translation flow (Python)
- LangflowAssistant.json: Main assistant flow for Q&A and component generation (JSON)

可用流程：
- translation_flow：意图分类和翻译流程（Python 实现）
- LangflowAssistant.json：问答和组件生成的主助手流程（JSON 配置）
"""

# 从翻译流程模块中导入获取流程图的函数
from langflow.agentic.flows.translation_flow import get_graph as get_translation_flow_graph

# 定义模块的公共 API，仅导出翻译流程图获取函数
__all__ = [
    "get_translation_flow_graph",
]
