# LangChain 文本分割器
from langchain_text_splitters import CharacterTextSplitter

# 组件基类、输入/输出定义、数据模型
from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, IntInput, MessageTextInput, Output
from lfx.schema.data import Data
from lfx.utils.util import unescape_string


# 文本分割组件，按指定规则将文本拆分为块（已弃用）
class SplitTextComponent(Component):
    display_name: str = "Split Text"
    # 组件描述：根据指定条件将文本拆分为块
    description: str = "Split text into chunks based on specified criteria."
    icon = "scissors-line-dashed"
    name = "SplitText"

    inputs = [
        HandleInput(
            name="data_inputs",
            display_name="Data Inputs",
            info="The data to split.",
            input_types=["Data", "JSON"],
            is_list=True,
        ),
        IntInput(
            name="chunk_overlap",
            display_name="Chunk Overlap",
            info="Number of characters to overlap between chunks.",
            value=200,
        ),
        IntInput(
            name="chunk_size",
            display_name="Chunk Size",
            info="The maximum number of characters in each chunk.",
            value=1000,
        ),
        MessageTextInput(
            name="separator",
            display_name="Separator",
            info="The character to split on. Defaults to newline.",
            value="\n",
        ),
    ]

    outputs = [
        Output(display_name="Chunks", name="chunks", method="split_text"),
    ]

    # 将文档列表转换为 Data 列表
    def _docs_to_data(self, docs):
        return [Data(text=doc.page_content, data=doc.metadata) for doc in docs]

    # 分割文本并返回结果
    def split_text(self) -> list[Data]:
        separator = unescape_string(self.separator)

        documents = [_input.to_lc_document() for _input in self.data_inputs if isinstance(_input, Data)]

        splitter = CharacterTextSplitter(
            chunk_overlap=self.chunk_overlap,
            chunk_size=self.chunk_size,
            separator=separator,
        )
        docs = splitter.split_documents(documents)
        data = self._docs_to_data(docs)
        self.status = data
        return data
