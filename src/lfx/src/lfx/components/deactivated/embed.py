# 自定义组件基类
from lfx.custom.custom_component.custom_component import CustomComponent

# 嵌入模型类型
from lfx.field_typing import Embeddings

# 数据模型
from lfx.schema.data import Data


# 文本嵌入组件，将文本转换为向量嵌入
class EmbedComponent(CustomComponent):
    display_name = "Embed Texts"
    name = "Embed"

    # 构建配置
    def build_config(self):
        return {"texts": {"display_name": "Texts"}, "embbedings": {"display_name": "Embeddings"}}

    # 构建方法：使用嵌入模型将文本转换为向量
    def build(self, texts: list[str], embbedings: Embeddings) -> Data:
        # 使用嵌入模型嵌入文档列表
        vectors = Data(vector=embbedings.embed_documents(texts))
        self.status = vectors
        return vectors
