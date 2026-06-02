from typing import Any
from urllib.parse import urljoin

import httpx

from lfx.base.embeddings.model import LCEmbeddingsModel
from lfx.field_typing import Embeddings
from lfx.inputs.inputs import DropdownInput, SecretStrInput
from lfx.io import FloatInput, MessageTextInput


# LM Studio 嵌入模型组件，基于 NVIDIA AI Endpoints 的嵌入实现
class LMStudioEmbeddingsComponent(LCEmbeddingsModel):
    display_name: str = "LM Studio Embeddings"
    # 组件描述：使用 LM Studio 生成文本嵌入向量
    description: str = "Generate embeddings using LM Studio."
    icon = "LMStudio"

    # 当用户点击刷新按钮或更改模型下拉选项时，动态更新可用模型列表
    async def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None):  # noqa: ARG002
        if field_name == "model":
            base_url_dict = build_config.get("base_url", {})
            base_url_load_from_db = base_url_dict.get("load_from_db", False)
            base_url_value = base_url_dict.get("value")
            # 如果 base_url 是从数据库加载的变量引用，则解析其实际值
            if base_url_load_from_db:
                base_url_value = await self.get_variables(base_url_value, field_name)
            # 如果未配置 base_url，则使用默认的本地 LM Studio 地址
            elif not base_url_value:
                base_url_value = "http://localhost:1234/v1"
            # 从 LM Studio 服务器获取可用模型列表并填充到下拉选项中
            build_config["model"]["options"] = await self.get_model(base_url_value)

        return build_config

    # 从 LM Studio 服务器获取当前可用的嵌入模型列表
    @staticmethod
    async def get_model(base_url_value: str) -> list[str]:
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

    # 组件的输入参数定义
    inputs = [
        # 模型选择下拉框，支持从服务器动态刷新可用模型列表
        DropdownInput(
            name="model",
            display_name="Model",
            advanced=False,
            refresh_button=True,
            required=True,
        ),
        # LM Studio 服务的基础 URL 地址
        MessageTextInput(
            name="base_url",
            display_name="LM Studio Base URL",
            refresh_button=True,
            value="http://localhost:1234/v1",
            required=True,
        ),
        # LM Studio API 密钥，用于身份验证
        SecretStrInput(
            name="api_key",
            display_name="LM Studio API Key",
            advanced=True,
            value="LMSTUDIO_API_KEY",
        ),
        # 模型温度参数，控制嵌入生成的随机性
        FloatInput(
            name="temperature",
            display_name="Model Temperature",
            value=0.1,
            advanced=True,
        ),
    ]

    # 构建并返回嵌入模型实例，使用 NVIDIA AI Endpoints 的嵌入实现
    def build_embeddings(self) -> Embeddings:
        try:
            from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
        except ImportError as e:
            msg = "Please install langchain-nvidia-ai-endpoints to use LM Studio Embeddings."
            raise ImportError(msg) from e
        try:
            output = NVIDIAEmbeddings(
                model=self.model,
                base_url=self.base_url,
                temperature=self.temperature,
                nvidia_api_key=self.api_key,
            )
        except Exception as e:
            msg = f"Could not connect to LM Studio API. Error: {e}"
            raise ValueError(msg) from e
        return output
