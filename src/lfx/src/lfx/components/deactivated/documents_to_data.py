# LangChain 文档类型
from langchain_core.documents import Document

# 自定义组件基类
from lfx.custom.custom_component.custom_component import CustomComponent

# 数据模型
from lfx.schema.data import Data


# 文档转数据组件，将 LangChain Document 转换为 Data 对象
class DocumentsToDataComponent(CustomComponent):
    display_name = "Documents ⇢ Data"
    description = "Convert LangChain Documents into Data."
    icon = "LangChain"
    name = "DocumentsToData"

    # 字段配置
    field_config = {
        "documents": {"display_name": "Documents"},
    }

    # 构建方法：将文档列表转换为数据列表
    def build(self, documents: list[Document]) -> list[Data]:
        # 如果输入是单个文档，转换为列表
        if isinstance(documents, Document):
            documents = [documents]
        # 将每个文档转换为 Data 对象
        data = [Data.from_document(document) for document in documents]
        self.status = data
        return data
