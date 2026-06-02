from lfx.custom.custom_component.component import Component
from lfx.field_typing import Embeddings
from lfx.io import Output


# 嵌入模型基类，所有嵌入模型组件应继承此类
class LCEmbeddingsModel(Component):
    # 追踪类型标识为嵌入
    trace_type = "embedding"

    # 输出定义：嵌入模型组件的输出
    outputs = [
        Output(display_name="Embedding Model", name="embeddings", method="build_embeddings"),
    ]

    # 验证输出配置，确保必需的输出方法已正确定义
    def _validate_outputs(self) -> None:
        required_output_methods = ["build_embeddings"]
        output_names = [output.name for output in self.outputs]
        for method_name in required_output_methods:
            if method_name not in output_names:
                msg = f"Output with name '{method_name}' must be defined."
                raise ValueError(msg)
            if not hasattr(self, method_name):
                msg = f"Method '{method_name}' must be defined."
                raise ValueError(msg)

    # 构建嵌入模型，子类必须实现此方法
    def build_embeddings(self) -> Embeddings:
        msg = "You must implement the build_embeddings method in your class."
        raise NotImplementedError(msg)
