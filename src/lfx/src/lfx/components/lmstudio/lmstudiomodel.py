from typing import Any
from urllib.parse import urljoin

import httpx
from langchain_openai import ChatOpenAI

from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import DictInput, DropdownInput, FloatInput, IntInput, SecretStrInput, StrInput


class LMStudioModelComponent(LCModelComponent):
    """LM Studio 模型组件，用于通过 LM Studio 本地大语言模型生成文本。

    该组件基于 LangChain 的 ChatOpenAI 接口，连接本地运行的 LM Studio 服务，
    支持自动发现可用模型列表，并提供温度、最大 token 数等生成参数的配置。
    """

    display_name = "LM Studio"
    description = "Generate text using LM Studio Local LLMs."
    icon = "LMStudio"
    name = "LMStudioModel"

    async def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None):  # noqa: ARG002
        """当用户在画布上修改构建配置时的回调方法。

        主要处理模型名称的变更：当 model_name 字段被修改时，
        会重新从 LM Studio 服务器获取可用模型列表并更新下拉选项。
        同时会检查 base_url 是否可访问，如果无法访问则给出提示信息。
        """
        if field_name == "model_name":
            # 从构建配置中获取 base_url 相关信息
            base_url_dict = build_config.get("base_url", {})
            base_url_load_from_db = base_url_dict.get("load_from_db", False)
            base_url_value = base_url_dict.get("value")
            # 如果 base_url 来自数据库（变量引用），则解析实际值
            if base_url_load_from_db:
                base_url_value = await self.get_variables(base_url_value, field_name)
            try:
                # 尝试访问 LM Studio 的模型列表接口，验证服务是否可达
                async with httpx.AsyncClient() as client:
                    response = await client.get(urljoin(base_url_value, "/v1/models"), timeout=2.0)
                    response.raise_for_status()
            except httpx.HTTPError:
                msg = "Could not access the default LM Studio URL. Please, specify the 'Base URL' field."
                self.log(msg)
                return build_config
            # 连接成功后，更新模型名称的下拉选项
            build_config["model_name"]["options"] = await self.get_model(base_url_value)

        return build_config

    @staticmethod
    async def get_model(base_url_value: str) -> list[str]:
        """从 LM Studio 服务器获取所有可用模型的 ID 列表。

        通过调用 LM Studio 的 OpenAI 兼容接口 /v1/models 获取模型列表，
        返回每个模型的 id 字段作为下拉选项。

        Args:
            base_url_value: LM Studio 服务器的基础 URL 地址。

        Returns:
            可用模型 ID 的字符串列表。

        Raises:
            ValueError: 当无法连接 LM Studio 服务器或获取模型列表失败时抛出。
        """
        try:
            url = urljoin(base_url_value, "/v1/models")
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            msg = "Could not retrieve models. Please, make sure the LM Studio server is running."
            raise ValueError(msg) from e

    # 组件输入参数定义
    inputs = [
        # 继承基础模型组件的所有通用输入参数
        *LCModelComponent.get_base_inputs(),
        # 最大生成 token 数，设为 0 表示不限制
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            advanced=True,
            info="The maximum number of tokens to generate. Set to 0 for unlimited tokens.",
            range_spec=RangeSpec(min=0, max=128000),
        ),
        # 传递给模型的额外参数（如 top_p、frequency_penalty 等）
        DictInput(name="model_kwargs", display_name="Model Kwargs", advanced=True),
        # 模型名称下拉选择框，支持刷新按钮从服务器重新获取可用模型
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            advanced=False,
            refresh_button=True,
        ),
        # LM Studio 服务的 API 地址，默认为本地 1234 端口
        StrInput(
            name="base_url",
            display_name="Base URL",
            advanced=False,
            info="Endpoint of the LM Studio API. Defaults to 'http://localhost:1234/v1' if not specified.",
            value="http://localhost:1234/v1",
        ),
        # API 密钥（可选），用于需要认证的 LM Studio 部署
        SecretStrInput(
            name="api_key",
            display_name="LM Studio API Key",
            info="The LM Studio API Key to use for LM Studio.",
            advanced=True,
            value="LMSTUDIO_API_KEY",
        ),
        # 生成温度，控制输出的随机性，值越高越随机
        FloatInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            advanced=True,
        ),
        # 随机种子，用于确保生成结果的可复现性
        IntInput(
            name="seed",
            display_name="Seed",
            info="The seed controls the reproducibility of the job.",
            advanced=True,
            value=1,
        ),
    ]

    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        """根据用户配置构建 LangChain 的 ChatOpenAI 模型实例。

        LM Studio 提供了与 OpenAI 兼容的 API 接口，因此这里复用 ChatOpenAI
        客户端来连接本地 LM Studio 服务。

        Returns:
            配置好的 ChatOpenAI 语言模型实例。
        """
        lmstudio_api_key = self.api_key
        temperature = self.temperature
        model_name: str = self.model_name
        max_tokens = self.max_tokens
        model_kwargs = self.model_kwargs or {}
        base_url = self.base_url or "http://localhost:1234/v1"
        seed = self.seed

        return ChatOpenAI(
            max_tokens=max_tokens or None,
            model_kwargs=model_kwargs,
            model=model_name,
            base_url=base_url,
            api_key=lmstudio_api_key,
            temperature=temperature if temperature is not None else 0.1,
            seed=seed,
        )

    def _get_exception_message(self, e: Exception):
        """Get a message from an LM Studio exception.

        从 LM Studio 异常中提取可读的错误消息。
        主要处理 OpenAI 的 BadRequestError 类型异常，从中提取服务端返回的具体错误信息。

        Args:
            e (Exception): The exception to get the message from.
            需要提取错误信息的异常对象。

        Returns:
            str: The message from the exception.
            异常中的错误消息，如果没有则返回 None。
        """
        try:
            from openai import BadRequestError
        except ImportError:
            return None
        if isinstance(e, BadRequestError):
            message = e.body.get("message")
            if message:
                return message
        return None
