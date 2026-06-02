# 多查询检索器的 LangChain 集成
from langchain_classic.retrievers import MultiQueryRetriever

# 提示模板
from langchain_core.prompts import PromptTemplate

# 自定义组件基类
from lfx.custom.custom_component.custom_component import CustomComponent

# 类型定义
from lfx.field_typing import BaseRetriever, LanguageModel, Text

# 输入组件类型
from lfx.inputs.inputs import HandleInput, StrInput


# 多查询检索器组件，使用 LLM 生成多个查询以提高检索效果
class MultiQueryRetrieverComponent(CustomComponent):
    display_name = "MultiQueryRetriever"
    description = "Initialize from llm using default template."
    documentation = "https://python.langchain.com/docs/modules/data_connection/retrievers/how_to/MultiQueryRetriever"
    name = "MultiQueryRetriever"
    legacy = True

    # 输入参数定义
    inputs = [
        # 语言模型
        HandleInput(
            name="llm",
            display_name="LLM",
            input_types=["LanguageModel"],
            required=True,
        ),
        HandleInput(
            name="retriever",
            display_name="Retriever",
            input_types=["BaseRetriever"],
            required=True,
        ),
        StrInput(
            name="prompt",
            display_name="Prompt",
            value="You are an AI language model assistant. Your task is \n"
            "to generate 3 different versions of the given user \n"
            "question to retrieve relevant documents from a vector database. \n"
            "By generating multiple perspectives on the user question, \n"
            "your goal is to help the user overcome some of the limitations \n"
            "of distance-based similarity search. Provide these alternative \n"
            "questions separated by newlines. Original question: {question}",
            required=False,
        ),
        StrInput(
            name="parser_key",
            display_name="Parser Key",
            value="lines",
            required=False,
        ),
    ]

    def build(
        self,
        llm: LanguageModel,
        retriever: BaseRetriever,
        prompt: Text | None = None,
        parser_key: str = "lines",
    ) -> MultiQueryRetriever:
        if not prompt:
            return MultiQueryRetriever.from_llm(llm=llm, retriever=retriever, parser_key=parser_key)
        prompt_template = PromptTemplate.from_template(prompt)
        return MultiQueryRetriever.from_llm(llm=llm, retriever=retriever, prompt=prompt_template, parser_key=parser_key)
