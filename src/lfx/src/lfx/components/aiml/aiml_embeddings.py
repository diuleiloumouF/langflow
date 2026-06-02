# AIML 嵌入组件模块
# 该模块提供了基于 AI/ML API 的嵌入生成组件，支持多种文本嵌入模型

from lfx.base.embeddings.aiml_embeddings import AIMLEmbeddingsImpl  # AIML 嵌入实现类
from lfx.base.embeddings.model import LCEmbeddingsModel  # 嵌入模型基类
from lfx.field_typing import Embeddings  # 嵌入类型定义
from lfx.inputs.inputs import DropdownInput  # 下拉选择输入组件
from lfx.io import SecretStrInput  # 密钥字符串输入组件


class AIMLEmbeddingsComponent(LCEmbeddingsModel):
    """AI/ML API 嵌入组件

    该组件封装了 AI/ML API 的嵌入生成功能，允许用户通过可视化界面
    选择嵌入模型并配置 API 密钥，从而生成文本嵌入向量。

    支持的模型：
    - text-embedding-3-small: 小型文本嵌入模型
    - text-embedding-3-large: 大型文本嵌入模型
    - text-embedding-ada-002: Ada-002 文本嵌入模型
    """

    # 组件显示名称，用于在 Langflow 画布上显示
    display_name = "AI/ML API Embeddings"
    # 组件描述信息
    description = "Generate embeddings using the AI/ML API."
    # 组件图标
    icon = "AIML"
    # 组件内部名称，用于代码中引用
    name = "AIMLEmbeddings"

    # 组件输入参数定义
    inputs = [
        # 模型名称下拉选择框
        DropdownInput(
            name="model_name",  # 参数名称
            display_name="Model Name",  # 显示名称
            options=[  # 可选模型列表
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            ],
            required=True,  # 必填参数
        ),
        # API 密钥输入框（密文显示）
        SecretStrInput(
            name="aiml_api_key",  # 参数名称
            display_name="AI/ML API Key",  # 显示名称
            value="AIML_API_KEY",  # 环境变量名称，用于自动填充
            required=True,  # 必填参数
        ),
    ]

    def build_embeddings(self) -> Embeddings:
        """构建嵌入模型实例

        根据用户配置的参数（API 密钥和模型名称）创建并返回
        AIMLEmbeddingsImpl 实例，用于后续的文本嵌入生成。

        Returns:
            Embeddings: 嵌入模型实例，可用于生成文本嵌入向量
        """
        return AIMLEmbeddingsImpl(
            api_key=self.aiml_api_key,  # API 密钥
            model=self.model_name,  # 模型名称
        )
