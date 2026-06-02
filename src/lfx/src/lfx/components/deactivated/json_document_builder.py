# JSON Document Builder
# JSON 文档构建器

# Build a Document containing a JSON object using a key and another Document page content.
# 使用键和另一个 Document 页面内容构建包含 JSON 对象的 Document。

# **Params**
# **参数**

# - **Key:** The key to use for the JSON object.
# - **Key:** 用于 JSON 对象的键。
# - **Document:** The Document page to use for the JSON object.
# - **Document:** 用于 JSON 对象的 Document 页面。

# **Output**
# **输出**

# - **Document:** The Document containing the JSON object.
# - **Document:** 包含 JSON 对象的 Document。


# 高性能 JSON 序列化库
import orjson

# LangChain 文档类型
from langchain_core.documents import Document

# 自定义组件基类
from lfx.custom.custom_component.custom_component import CustomComponent

# 输入组件类型
from lfx.io import HandleInput, StrInput


# JSON 文档构建器组件，将键值对构建为 JSON 格式的 Document
class JSONDocumentBuilder(CustomComponent):
    display_name: str = "JSON Document Builder"
    description: str = "Build a Document containing a JSON object using a key and another Document page content."
    name = "JSONDocumentBuilder"
    documentation: str = "https://docs.langflow.org/legacy-core-components"
    legacy = True

    # 输入参数定义
    inputs = [
        # JSON 对象的键名
        StrInput(
            name="key",
            display_name="Key",
            required=True,
        ),
        # 输入文档
        HandleInput(
            name="document",
            display_name="Document",
            required=True,
        ),
    ]

    # 构建方法：将键值对构建为 JSON 格式的 Document
    def build(
        self,
        key: str,
        document: Document,
    ) -> Document:
        documents = None
        if isinstance(document, list):
            # 处理文档列表：将每个文档的页面内容包装为 JSON
            documents = [Document(page_content=orjson.dumps({key: doc.page_content}).decode()) for doc in document]
        elif isinstance(document, Document):
            # 处理单个文档：将页面内容包装为 JSON
            documents = Document(page_content=orjson.dumps({key: document.page_content}).decode())
        else:
            msg = f"Expected Document or list of Documents, got {type(document)}"
            raise TypeError(msg)

        self.repr_value = documents
        return documents
