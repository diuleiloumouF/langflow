# 导入 MistralAI 的 Embeddings 实现
from langchain_mistralai import MistralAIEmbeddings

# 导入 SecretStr 用于安全地处理 API 密钥
from pydantic.v1 import SecretStr

# 导入 LangFlow 组件基类
from lfx.base.models.model import LCModelComponent

# 导入 Embeddings 类型定义
from lfx.field_typing import Embeddings

# 导入组件输入/输出接口定义
from lfx.io import DropdownInput, IntInput, MessageTextInput, Output, SecretStrInput


# MistralAI Embeddings 组件
# 用于通过 MistralAI 模型生成文本向量嵌入（embeddings）的组件
class MistralAIEmbeddingsComponent(LCModelComponent):
    # 组件在画布上显示的名称
    display_name = "MistralAI Embeddings"
    # 组件功能描述
    description = "Generate embeddings using MistralAI models."
    # 组件图标
    icon = "MistralAI"
    # 组件内部唯一标识名
    name = "MistalAIEmbeddings"

    # 组件输入参数定义
    inputs = [
        # 嵌入模型选择下拉框，当前仅支持 mistral-embed
        DropdownInput(
            name="model",
            display_name="Model",
            advanced=False,
            options=["mistral-embed"],
            value="mistral-embed",
        ),
        # Mistral API 密钥输入（必填，密钥类型）
        SecretStrInput(name="mistral_api_key", display_name="Mistral API Key", required=True),
        # 最大并发请求数（高级参数）
        IntInput(
            name="max_concurrent_requests",
            display_name="Max Concurrent Requests",
            advanced=True,
            value=64,
        ),
        # 最大重试次数（高级参数）
        IntInput(name="max_retries", display_name="Max Retries", advanced=True, value=5),
        # 请求超时时间（秒）（高级参数）
        IntInput(name="timeout", display_name="Request Timeout", advanced=True, value=120),
        # API 端点地址（高级参数），默认为 Mistral 官方 API 地址
        MessageTextInput(
            name="endpoint",
            display_name="API Endpoint",
            advanced=True,
            value="https://api.mistral.ai/v1/",
        ),
    ]

    # 组件输出参数定义，输出一个 Embeddings 实例
    outputs = [
        Output(display_name="Embeddings", name="embeddings", method="build_embeddings"),
    ]

    # 构建并返回 MistralAI Embeddings 实例
    def build_embeddings(self) -> Embeddings:
        # 检查 API 密钥是否提供
        if not self.mistral_api_key:
            msg = "Mistral API Key is required"
            raise ValueError(msg)

        # 将密钥字符串转换为 SecretStr 并提取明文值
        api_key = SecretStr(self.mistral_api_key).get_secret_value()

        # 创建并返回 MistralAI Embeddings 实例，传入所有配置参数
        return MistralAIEmbeddings(
            api_key=api_key,
            model=self.model,
            endpoint=self.endpoint,
            max_concurrent_requests=self.max_concurrent_requests,
            max_retries=self.max_retries,
            timeout=self.timeout,
        )
