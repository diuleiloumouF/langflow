# 类型注解支持
from typing import Any

# Cohere SDK 客户端
import cohere

# Cohere 嵌入模型的 LangChain 集成
from langchain_cohere import CohereEmbeddings

# 模型组件基类
from lfx.base.models.model import LCModelComponent

# 嵌入模型类型
from lfx.field_typing import Embeddings

# 输入组件类型
from lfx.io import DropdownInput, FloatInput, IntInput, MessageTextInput, Output, SecretStrInput

# HTTP 成功状态码常量
HTTP_STATUS_OK = 200


# Cohere 嵌入组件，用于生成文本嵌入向量
class CohereEmbeddingsComponent(LCModelComponent):
    display_name = "Cohere Embeddings"
    description = "Generate embeddings using Cohere models."
    icon = "Cohere"
    name = "CohereEmbeddings"

    # 输入参数定义
    inputs = [
        # Cohere API 密钥
        SecretStrInput(name="api_key", display_name="Cohere API Key", required=True, real_time_refresh=True),
        # 嵌入模型名称（支持下拉选择和自定义输入）
        DropdownInput(
            name="model_name",
            display_name="Model",
            advanced=False,
            options=[
                "embed-english-v2.0",
                "embed-multilingual-v2.0",
                "embed-english-light-v2.0",
                "embed-multilingual-light-v2.0",
            ],
            value="embed-english-v2.0",
            refresh_button=True,
            combobox=True,
        ),
        # 文本截断方式
        MessageTextInput(name="truncate", display_name="Truncate", advanced=True),
        # 最大重试次数
        IntInput(name="max_retries", display_name="Max Retries", value=3, advanced=True),
        # 用户代理标识
        MessageTextInput(name="user_agent", display_name="User Agent", advanced=True, value="langchain"),
        # 请求超时时间
        FloatInput(name="request_timeout", display_name="Request Timeout", advanced=True),
    ]

    # 输出参数定义
    outputs = [
        Output(display_name="Embeddings", name="embeddings", method="build_embeddings"),
    ]

    # 构建 Cohere 嵌入模型实例
    def build_embeddings(self) -> Embeddings:
        data = None
        try:
            data = CohereEmbeddings(
                cohere_api_key=self.api_key,
                model=self.model_name,
                truncate=self.truncate,
                max_retries=self.max_retries,
                user_agent=self.user_agent,
                request_timeout=self.request_timeout or None,
            )
        except Exception as e:
            msg = (
                "Unable to create Cohere Embeddings. ",
                "Please verify the API key and model parameters, and try again.",
            )
            raise ValueError(msg) from e
        # 添加状态信息，避免返回数据被序列化为状态
        return data

    # 获取可用的 Cohere 嵌入模型列表
    def get_model(self):
        try:
            co = cohere.ClientV2(self.api_key)
            response = co.models.list(endpoint="embed")
            models = response.models
            return [model.name for model in models]
        except Exception as e:
            msg = f"Failed to fetch Cohere models. Error: {e}"
            raise ValueError(msg) from e

    # 动态更新构建配置，当 API 密钥或模型名称变更时刷新模型选项
    async def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None):
        if field_name in {"model_name", "api_key"}:
            if build_config.get("api_key", {}).get("value", None):
                build_config["model_name"]["options"] = self.get_model()
        else:
            build_config["model_name"]["options"] = field_value
        return build_config
