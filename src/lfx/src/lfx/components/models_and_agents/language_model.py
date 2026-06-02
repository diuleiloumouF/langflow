# 语言模型组件
# 该组件封装了多种语言模型提供商（如 OpenAI、IBM watsonx.ai、Ollama 等），
# 允许用户在可视化流程中统一使用不同供应商的语言模型。

from lfx.base.models.model import LCModelComponent
from lfx.base.models.unified_models import (
    get_llm,
    handle_model_input_update,
)
from lfx.base.models.watsonx_constants import IBM_WATSONX_URLS
from lfx.field_typing.constants import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import BoolInput, DropdownInput, StrInput
from lfx.io import IntInput, MessageInput, ModelInput, MultilineInput, SecretStrInput, SliderInput

# Ollama 本地服务的默认地址
DEFAULT_OLLAMA_URL = "http://localhost:11434"


class LanguageModelComponent(LCModelComponent):
    """语言模型组件：根据用户选择的提供商运行对应的语言模型。

    支持的提供商包括 OpenAI、IBM watsonx.ai、Ollama 等。
    用户可通过画布配置模型选择、API 密钥、系统消息、温度等参数。
    """

    # 组件在画布上显示的名称
    display_name = "Language Model"
    # 组件的功能描述
    description = "Runs a language model given a specified provider."
    # 组件的文档链接
    documentation: str = "https://docs.langflow.org/components-models"
    # 组件图标
    icon = "brain-circuit"
    # 组件所属分类
    category = "models"

    # 组件的输入参数列表
    inputs = [
        # 模型选择下拉框：用户在此选择具体的模型提供商和模型名称
        ModelInput(
            name="model",
            display_name="Language Model",
            info="Select your model provider",
            real_time_refresh=True,
            required=True,
        ),
        # API 密钥输入框：用于覆盖全局的提供商设置，留空则使用预配置的密钥
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            info="Overrides global provider settings. Leave blank to use your pre-configured API Key.",
            required=False,
            show=True,
            real_time_refresh=True,
            advanced=True,
        ),
        # IBM watsonx.ai 的 API 端点选择，仅在选择 watsonx 提供商时显示
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
        # IBM watsonx.ai 的项目 ID，仅在选择 watsonx 提供商时显示
        StrInput(
            name="project_id",
            display_name="watsonx Project ID",
            info="The project ID associated with the foundation model (IBM watsonx.ai only)",
            show=False,
            required=False,
        ),
        # Ollama 本地服务的 API 地址，仅在选择 Ollama 提供商时显示
        StrInput(
            name="ollama_base_url",
            display_name="Ollama API URL",
            info=f"Endpoint of the Ollama API (Ollama only). Defaults to {DEFAULT_OLLAMA_URL}",
            value=DEFAULT_OLLAMA_URL,
            show=False,
            real_time_refresh=True,
        ),
        # 用户输入文本：发送给模型的输入消息
        MessageInput(
            name="input_value",
            display_name="Input",
            info="The input text to send to the model",
        ),
        # 系统提示词：用于设定助手的行为和角色
        MultilineInput(
            name="system_message",
            display_name="System Message",
            info="A system message that helps set the behavior of the assistant",
            advanced=False,
        ),
        # 是否启用流式输出
        BoolInput(
            name="stream",
            display_name="Stream",
            info="Whether to stream the response",
            value=False,
            advanced=True,
        ),
        # 温度参数：控制模型输出的随机性，值越高越随机
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            info="Controls randomness in responses",
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            advanced=True,
        ),
        # 最大 token 数：限制模型生成的最大长度
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            info="Maximum number of tokens to generate. Field name varies by provider.",
            advanced=True,
            range_spec=RangeSpec(min=1, max=128000, step=1, step_type="int"),
        ),
    ]

    def build_model(self) -> LanguageModel:
        """构建并返回语言模型实例。

        根据用户在画布上选择的模型和参数，调用统一的 get_llm 工厂函数
        创建对应提供商的语言模型对象。
        """
        return get_llm(
            model=self.model,
            user_id=self.user_id,
            api_key=self.api_key,
            temperature=self.temperature,
            stream=self.stream,
            max_tokens=getattr(self, "max_tokens", None),
            watsonx_url=getattr(self, "base_url_ibm_watsonx", None),
            watsonx_project_id=getattr(self, "project_id", None),
            ollama_base_url=getattr(self, "ollama_base_url", None),
        )

    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        """Dynamically update build config with user-filtered model options."""
        # 动态更新构建配置：根据用户当前选择的提供商，过滤并刷新可用的模型选项列表
        return handle_model_input_update(self, build_config, field_value, field_name)
