# LiteLLM 聊天模型的 LangChain 集成
from langchain_community.chat_models.litellm import ChatLiteLLM, ChatLiteLLMException

# 流式输出信息文本常量
from lfx.base.constants import STREAM_INFO_TEXT

# 模型组件基类
from lfx.base.models.model import LCModelComponent

# 语言模型类型
from lfx.field_typing import LanguageModel

# 输入组件类型
from lfx.io import (
    BoolInput,
    DictInput,
    DropdownInput,
    FloatInput,
    IntInput,
    MessageInput,
    SecretStrInput,
    StrInput,
)


# LiteLLM 聊天模型组件，支持多种 LLM 提供者
class ChatLiteLLMModelComponent(LCModelComponent):
    display_name = "LiteLLM"
    description = "`LiteLLM` collection of large language models."
    documentation = "https://python.langchain.com/docs/integrations/chat/litellm"
    icon = "🚄"

    # 输入参数定义
    inputs = [
        # 输入消息
        MessageInput(name="input_value", display_name="Input"),
        # 模型名称
        StrInput(
            name="model",
            display_name="Model name",
            advanced=False,
            required=True,
            info="The name of the model to use. For example, `gpt-3.5-turbo`.",
        ),
        # API 密钥
        SecretStrInput(
            name="api_key",
            display_name="Chat LiteLLM API Key",
            advanced=False,
            required=False,
        ),
        # API 提供者选择
        DropdownInput(
            name="provider",
            display_name="Provider",
            info="The provider of the API key.",
            options=[
                "OpenAI",
                "Azure",
                "Anthropic",
                "Replicate",
                "Cohere",
                "OpenRouter",
            ],
        ),
        # 温度参数：控制生成文本的随机性
        FloatInput(
            name="temperature",
            display_name="Temperature",
            advanced=False,
            required=False,
            value=0.7,
        ),
        # 额外的关键词参数
        DictInput(
            name="kwargs",
            display_name="Kwargs",
            advanced=True,
            required=False,
            is_list=True,
            value={},
        ),
        # 模型特定的关键词参数
        DictInput(
            name="model_kwargs",
            display_name="Model kwargs",
            advanced=True,
            required=False,
            is_list=True,
            value={},
        ),
        # Top-p 采样参数
        FloatInput(name="top_p", display_name="Top p", advanced=True, required=False, value=0.5),
        # Top-k 采样参数
        IntInput(name="top_k", display_name="Top k", advanced=True, required=False, value=35),
        # 每个提示生成的补全数量
        IntInput(
            name="n",
            display_name="N",
            advanced=True,
            required=False,
            info="Number of chat completions to generate for each prompt. "
            "Note that the API may not return the full n completions if duplicates are generated.",
            value=1,
        ),
        # 最大生成 token 数量
        IntInput(
            name="max_tokens",
            display_name="Max tokens",
            advanced=False,
            value=256,
            info="The maximum number of tokens to generate for each chat completion.",
        ),
        # 最大重试次数
        IntInput(
            name="max_retries",
            display_name="Max retries",
            advanced=True,
            required=False,
            value=6,
        ),
        # 详细输出模式
        BoolInput(
            name="verbose",
            display_name="Verbose",
            advanced=True,
            required=False,
            value=False,
        ),
        # 流式输出开关
        BoolInput(
            name="stream",
            display_name="Stream",
            info=STREAM_INFO_TEXT,
            advanced=True,
        ),
        # 系统消息
        StrInput(
            name="system_message",
            display_name="System Message",
            info="System message to pass to the model.",
            advanced=True,
        ),
    ]

    # 构建 LiteLLM 聊天模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        try:
            import litellm

            # 配置 litellm：丢弃不支持的参数，设置详细模式
            litellm.drop_params = True
            litellm.set_verbose = self.verbose
        except ImportError as e:
            msg = "Could not import litellm python package. Please install it with `pip install litellm`"
            raise ChatLiteLLMException(msg) from e
        # 移除空键值对
        if "" in self.kwargs:
            del self.kwargs[""]
        if "" in self.model_kwargs:
            del self.model_kwargs[""]
        # Azure 提供者需要检查必要字段
        if self.provider == "Azure":
            if "api_base" not in self.kwargs:
                msg = "Missing api_base on kwargs"
                raise ValueError(msg)
            if "api_version" not in self.model_kwargs:
                msg = "Missing api_version on model_kwargs"
                raise ValueError(msg)
        # 构建 ChatLiteLLM 实例
        output = ChatLiteLLM(
            model=f"{self.provider.lower()}/{self.model}",
            client=None,
            streaming=self.stream,
            temperature=self.temperature,
            model_kwargs=self.model_kwargs if self.model_kwargs is not None else {},
            top_p=self.top_p,
            top_k=self.top_k,
            n=self.n,
            max_tokens=self.max_tokens,
            max_retries=self.max_retries,
            **self.kwargs,
        )
        # 设置 API 密钥
        output.client.api_key = self.api_key

        return output
