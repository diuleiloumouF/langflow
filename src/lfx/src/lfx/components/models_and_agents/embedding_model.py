from lfx.base.embeddings.model import LCEmbeddingsModel
from lfx.base.models.unified_models import (
    get_embedding_model_options,
    get_embeddings,
    handle_model_input_update,
)
from lfx.base.models.watsonx_constants import IBM_WATSONX_URLS
from lfx.field_typing import Embeddings
from lfx.io import (
    BoolInput,
    DictInput,
    DropdownInput,
    FloatInput,
    IntInput,
    MessageTextInput,
    ModelInput,
    SecretStrInput,
    StrInput,
)

# Ollama 本地服务的默认地址
DEFAULT_OLLAMA_URL = "http://localhost:11434"


class EmbeddingModelComponent(LCEmbeddingsModel):
    """Embedding 模型组件，支持多种模型提供商（OpenAI、Ollama、Watsonx 等）生成文本嵌入向量。"""

    display_name = "Embedding Model"
    description = "Generate embeddings using a specified provider."
    documentation: str = "https://docs.langflow.org/components-embedding-models"
    icon = "binary"
    name = "EmbeddingModel"
    category = "models"

    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        """根据用户选择的模型提供商，动态更新构建配置中的可用模型选项。"""
        return handle_model_input_update(
            self,
            dict(build_config),
            field_value,
            field_name,
            cache_key_prefix="embedding_model_options",
            get_options_func=get_embedding_model_options,
        )

    # 组件输入参数定义
    inputs = [
        # 模型选择：支持实时刷新的下拉框，类型为嵌入模型
        ModelInput(
            name="model",
            display_name="Embedding Model",
            info="Select your model provider",
            real_time_refresh=True,
            required=True,
            model_type="embedding",
            input_types=["Embeddings"],  # Override default to accept Embeddings instead of LanguageModel
        ),
        # API 密钥：可选，覆盖全局提供商设置
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            info="Overrides global provider settings. Leave blank to use your pre-configured API Key.",
            real_time_refresh=True,
            advanced=True,
        ),
        # API 基础地址：可选，留空使用默认值
        MessageTextInput(
            name="api_base",
            display_name="API Base URL",
            info="Base URL for the API. Leave empty for default.",
            advanced=True,
        ),
        # 以下为 IBM Watsonx 专用输入参数
        # Watsonx API 端点地址（组合框，支持手动输入）
        DropdownInput(
            name="base_url_ibm_watsonx",
            display_name="watsonx API Endpoint",
            info="The base URL of the API (IBM watsonx.ai only)",
            options=IBM_WATSONX_URLS,
            value=IBM_WATSONX_URLS[0],
            combobox=True,
            show=False,
            real_time_refresh=True,
        ),
        # Watsonx 项目 ID
        MessageTextInput(
            name="project_id",
            display_name="Project ID",
            info="IBM watsonx.ai Project ID (required for IBM watsonx.ai)",
            show=False,
        ),
        # 以下为 Ollama 专用输入参数
        StrInput(
            name="ollama_base_url",
            display_name="Ollama API URL",
            info=f"Endpoint of the Ollama API (Ollama only). Defaults to {DEFAULT_OLLAMA_URL}",
            value=DEFAULT_OLLAMA_URL,
            show=False,
            real_time_refresh=True,
        ),
        # 嵌入向量维度（仅部分模型支持）
        IntInput(
            name="dimensions",
            display_name="Dimensions",
            info="The number of dimensions the resulting output embeddings should have. "
            "Only supported by certain models.",
            advanced=True,
        ),
        # 文本分块大小，用于处理长文本
        IntInput(
            name="chunk_size",
            display_name="Chunk Size",
            advanced=True,
            value=1000,
        ),
        # 请求超时时间（秒）
        FloatInput(
            name="request_timeout",
            display_name="Request Timeout",
            advanced=True,
        ),
        # 最大重试次数
        IntInput(
            name="max_retries",
            display_name="Max Retries",
            advanced=True,
            value=3,
        ),
        # 是否显示进度条
        BoolInput(
            name="show_progress_bar",
            display_name="Show Progress Bar",
            advanced=True,
        ),
        # 模型额外参数（字典形式），传递给支持该参数的提供商
        DictInput(
            name="model_kwargs",
            display_name="Model Kwargs",
            advanced=True,
            info=(
                "Additional keyword arguments to pass to the model. Only used by providers that support this parameter "
                "(e.g. OpenAI, Google Generative AI). "
                "Ignored for providers that do not include it in their parameter mapping."
            ),
        ),
        # Watsonx 输入截断 token 数（默认隐藏）
        IntInput(
            name="truncate_input_tokens",
            display_name="Truncate Input Tokens",
            advanced=True,
            value=200,
            show=False,
        ),
        # 是否在输出中包含原始文本（默认隐藏）
        BoolInput(
            name="input_text",
            display_name="Include the original text in the output",
            value=True,
            advanced=True,
            show=False,
        ),
    ]

    def build_embeddings(self) -> Embeddings:
        """根据选定的模型构建并返回嵌入实例。"""
        return get_embeddings(
            model=self.model,
            user_id=self.user_id,
            api_key=self.api_key,
            api_base=self.api_base,
            dimensions=self.dimensions,
            chunk_size=self.chunk_size,
            request_timeout=self.request_timeout,
            max_retries=self.max_retries,
            show_progress_bar=self.show_progress_bar,
            model_kwargs=self.model_kwargs,
            watsonx_url=getattr(self, "base_url_ibm_watsonx", None),
            watsonx_project_id=getattr(self, "project_id", None),
            watsonx_truncate_input_tokens=getattr(self, "truncate_input_tokens", None),
            watsonx_input_text=getattr(self, "input_text", None),
            ollama_base_url=getattr(self, "ollama_base_url", None),
        )
