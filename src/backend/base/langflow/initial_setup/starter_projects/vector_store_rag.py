# 向量存储 RAG 入门项目
# 该模块构建一个完整的 RAG（检索增强生成）流程，包含数据摄入和查询两个子图

from textwrap import dedent

from lfx.components.data import FileComponent
from lfx.components.datastax import AstraDBVectorStoreComponent
from lfx.components.input_output import ChatInput, ChatOutput
from lfx.components.models import LanguageModelComponent
from lfx.components.models_and_agents import PromptComponent
from lfx.components.openai.openai import OpenAIEmbeddingsComponent
from lfx.components.processing import ParserComponent
from lfx.components.processing.split_text import SplitTextComponent
from lfx.graph import Graph


def ingestion_graph():
    """构建数据摄入子图：文件加载 -> 文本分割 -> 嵌入 -> 向量存储。"""
    # Ingestion Graph
    file_component = FileComponent()
    text_splitter = SplitTextComponent()
    text_splitter.set(data_inputs=file_component.load_files_message)
    openai_embeddings = OpenAIEmbeddingsComponent()
    vector_store = AstraDBVectorStoreComponent()
    vector_store.set(
        embedding_model=openai_embeddings.build_embeddings,
        ingest_data=text_splitter.split_text,
    )

    return Graph(file_component, vector_store)


def rag_graph():
    """构建 RAG 查询子图：用户输入 -> 向量搜索 -> 数据解析 -> 提示词模板 -> 语言模型 -> 输出。"""
    # RAG Graph
    openai_embeddings = OpenAIEmbeddingsComponent()
    chat_input = ChatInput()
    rag_vector_store = AstraDBVectorStoreComponent()
    rag_vector_store.set(
        search_query=chat_input.message_response,
        embedding_model=openai_embeddings.build_embeddings,
    )

    parse_data = ParserComponent()
    parse_data.set(input_data=rag_vector_store.search_documents)
    prompt_component = PromptComponent()
    prompt_component.set(
        template=dedent("""Given the following context, answer the question.
                         Context:{context}

                         Question: {question}
                         Answer:"""),
        context=parse_data.parse_combined_text,
        question=chat_input.message_response,
    )

    openai_component = LanguageModelComponent()
    openai_component.set(input_value=prompt_component.build_prompt)

    chat_output = ChatOutput()
    chat_output.set(input_value=openai_component.text_response)

    return Graph(start=chat_input, end=chat_output)


def vector_store_rag_graph():
    """构建完整的向量存储 RAG 图，组合摄入和查询两个子图。"""
    return ingestion_graph() + rag_graph()
