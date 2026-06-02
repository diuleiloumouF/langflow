# 初始设置加载模块
# 该模块提供入门项目图的加载和序列化功能

from .starter_projects import (
    basic_prompting_graph,
    blog_writer_graph,
    document_qa_graph,
    memory_chatbot_graph,
    vector_store_rag_graph,
)


def get_starter_projects_graphs():
    """获取所有入门项目图的实例列表。"""
    return [
        basic_prompting_graph(),
        blog_writer_graph(),
        document_qa_graph(),
        memory_chatbot_graph(),
        vector_store_rag_graph(),
    ]


def get_starter_projects_dump():
    """获取所有入门项目图的序列化（JSON）表示。"""
    return [g.dump() for g in get_starter_projects_graphs()]
