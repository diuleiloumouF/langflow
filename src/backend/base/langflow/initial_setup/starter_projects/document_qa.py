# 文档问答入门项目
# 该模块构建一个文档问答流程：文件加载 -> 用户输入 -> 提示词模板 -> 语言模型 -> 输出

from lfx.components.data import FileComponent
from lfx.components.input_output import ChatInput, ChatOutput
from lfx.components.models import LanguageModelComponent
from lfx.components.models_and_agents import PromptComponent
from lfx.graph import Graph


def document_qa_graph(template: str | None = None):
    """构建文档问答示例图。"""
    if template is None:
        template = """Answer user's questions based on the document below:

---

{Document}

---

Question:
{Question}

Answer:
"""
    file_component = FileComponent()

    chat_input = ChatInput()
    prompt_component = PromptComponent()
    prompt_component.set(
        template=template,
        context=file_component.load_files_message,
        question=chat_input.message_response,
    )

    openai_component = LanguageModelComponent()
    openai_component.set(input_value=chat_input.message_response, system_message=prompt_component.build_prompt)

    chat_output = ChatOutput()
    chat_output.set(input_value=openai_component.text_response)

    return Graph(start=chat_input, end=chat_output)
