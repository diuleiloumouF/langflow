import asyncio
from typing import Any
from urllib.parse import urljoin

import httpx
from langchain_ollama import OllamaEmbeddings

from lfx.base.models.model import LCModelComponent
from lfx.field_typing import Embeddings
from lfx.io import DropdownInput, Output, SecretStrInput, StrInput
from lfx.log.logger import logger
from lfx.utils.util import transform_localhost_url

# HTTP 状态码常量，表示请求成功
HTTP_STATUS_OK = 200


class OllamaEmbeddingsComponent(LCModelComponent):
    # Ollama Embeddings 组件：通过 Ollama 本地模型生成文本向量嵌入
    display_name: str = "Ollama Embeddings"
    description: str = "Generate embeddings using Ollama models."
    documentation = "https://python.langchain.com/docs/integrations/text_embedding/ollama"
    icon = "Ollama"
    name = "OllamaEmbeddings"

    # Define constants for JSON keys
    # 用于解析 Ollama API 响应的 JSON 键名常量
    JSON_MODELS_KEY = "models"
    JSON_NAME_KEY = "name"
    JSON_CAPABILITIES_KEY = "capabilities"
    EMBEDDING_CAPABILITY = "embedding"

    # 组件输入参数定义
    inputs = [
        # 模型名称下拉选择框，支持实时刷新可选项列表
        DropdownInput(
            name="model_name",
            display_name="Ollama Model",
            value="",
            options=[],
            real_time_refresh=True,
            refresh_button=True,
            combobox=True,
            required=True,
        ),
        # Ollama 服务的基础 URL 地址
        StrInput(
            name="base_url",
            display_name="Ollama Base URL",
            info="Endpoint of the Ollama API. Defaults to http://localhost:11434.",
            value="http://localhost:11434",
            required=True,
            real_time_refresh=True,
        ),
        # Ollama API 密钥（可选，高级配置）
        SecretStrInput(
            name="api_key",
            display_name="Ollama API Key",
            info="Your Ollama API key.",
            value=None,
            required=False,
            real_time_refresh=True,
            advanced=True,
        ),
    ]

    # 组件输出定义：输出嵌入模型实例
    outputs = [
        Output(display_name="Embeddings", name="embeddings", method="build_embeddings"),
    ]

    @property
    def headers(self) -> dict[str, str] | None:
        """Get the headers for the Ollama API."""
        # 获取用于 Ollama API 请求的认证头信息
        if self.api_key and self.api_key.strip():
            return {"Authorization": f"Bearer {self.api_key}"}
        return None

    def build_embeddings(self) -> Embeddings:
        # 对基础 URL 进行本地地址转换处理
        transformed_base_url = transform_localhost_url(self.base_url)

        # Strip /v1 suffix if present
        # 如果 URL 以 /v1 结尾则移除，因为 Ollama 使用原生 API 而非 OpenAI 兼容 API
        if transformed_base_url and transformed_base_url.rstrip("/").endswith("/v1"):
            transformed_base_url = transformed_base_url.rstrip("/").removesuffix("/v1")
            logger.warning(
                "Detected '/v1' suffix in base URL. The Ollama component uses the native Ollama API, "
                "not the OpenAI-compatible API. The '/v1' suffix has been automatically removed. "
                "If you want to use the OpenAI-compatible API, please use the OpenAI component instead. "
                "Learn more at https://docs.ollama.com/openai#openai-compatibility"
            )

        # 构建 OllamaEmbeddings 所需的参数字典
        llm_params = {
            "model": self.model_name,
            "base_url": transformed_base_url,
        }

        # 如果存在认证头信息，则添加到请求参数中
        if self.headers:
            llm_params["client_kwargs"] = {"headers": self.headers}

        try:
            # 创建并返回 OllamaEmbeddings 实例
            output = OllamaEmbeddings(**llm_params)
        except Exception as e:
            msg = (
                "Unable to connect to the Ollama API. "
                "Please verify the base URL, ensure the relevant Ollama model is pulled, and try again."
            )
            raise ValueError(msg) from e
        return output

    async def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None):
        # 当 base_url 或 model_name 字段变更时，动态更新组件配置
        if field_name in {"base_url", "model_name"} and not await self.is_valid_ollama_url(self.base_url):
            msg = "Ollama is not running on the provided base URL. Please start Ollama and try again."
            raise ValueError(msg)
        if field_name in {"model_name", "base_url"}:
            # Use field_value if base_url is being updated, otherwise use self.base_url
            # 根据当前更新的字段决定使用哪个 URL 值
            base_url_to_check = field_value if field_name == "base_url" else self.base_url
            # Fallback to self.base_url if field_value is None or empty
            # 当字段值为空时回退到默认 URL
            if not base_url_to_check and field_name == "base_url":
                base_url_to_check = self.base_url
            logger.warning(f"Fetching Ollama models from updated URL: {base_url_to_check}")

            # 如果 URL 有效，则从 Ollama 服务获取可用模型列表并更新下拉选项
            if base_url_to_check and await self.is_valid_ollama_url(base_url_to_check):
                build_config["model_name"]["options"] = await self.get_model(base_url_to_check)
            else:
                build_config["model_name"]["options"] = []

        return build_config

    async def get_model(self, base_url_value: str) -> list[str]:
        """Get the model names from Ollama."""
        # 从 Ollama 服务获取所有支持 embedding 能力的模型名称列表
        try:
            # Strip /v1 suffix if present, as Ollama API endpoints are at root level
            # 清理 URL，移除 /v1 后缀并确保以 / 结尾
            base_url = base_url_value.rstrip("/").removesuffix("/v1")
            if not base_url.endswith("/"):
                base_url = base_url + "/"
            base_url = transform_localhost_url(base_url)

            # Ollama REST API to return models
            # 调用 Ollama 的 /api/tags 接口获取所有已拉取的模型
            tags_url = urljoin(base_url, "api/tags")

            # Ollama REST API to return model capabilities
            # 调用 Ollama 的 /api/show 接口获取模型详细能力信息
            show_url = urljoin(base_url, "api/show")

            async with httpx.AsyncClient() as client:
                headers = self.headers
                # Fetch available models
                # 获取可用模型列表
                tags_response = await client.get(url=tags_url, headers=headers)
                tags_response.raise_for_status()
                models = tags_response.json()
                if asyncio.iscoroutine(models):
                    models = await models
                await logger.adebug(f"Available models: {models}")

                # Filter models that are embedding models
                # 遍历模型列表，过滤出仅支持 embedding 能力的模型
                model_ids = []
                for model in models[self.JSON_MODELS_KEY]:
                    model_name = model[self.JSON_NAME_KEY]
                    await logger.adebug(f"Checking model: {model_name}")

                    # 查询每个模型的能力信息
                    payload = {"model": model_name}
                    show_response = await client.post(url=show_url, json=payload, headers=headers)
                    show_response.raise_for_status()
                    json_data = show_response.json()
                    if asyncio.iscoroutine(json_data):
                        json_data = await json_data

                    capabilities = json_data.get(self.JSON_CAPABILITIES_KEY, [])
                    await logger.adebug(f"Model: {model_name}, Capabilities: {capabilities}")

                    # 仅保留具备 embedding 能力的模型
                    if self.EMBEDDING_CAPABILITY in capabilities:
                        model_ids.append(model_name)

        except (httpx.RequestError, ValueError) as e:
            msg = "Could not get model names from Ollama."
            raise ValueError(msg) from e

        return model_ids

    async def is_valid_ollama_url(self, url: str) -> bool:
        # 验证给定的 URL 是否是有效的 Ollama 服务地址
        try:
            async with httpx.AsyncClient() as client:
                url = transform_localhost_url(url)
                if not url:
                    return False
                # Strip /v1 suffix if present, as Ollama API endpoints are at root level
                # 清理 URL 并通过请求 /api/tags 接口判断服务是否可用
                url = url.rstrip("/").removesuffix("/v1")
                if not url.endswith("/"):
                    url = url + "/"
                return (
                    await client.get(url=urljoin(url, "api/tags"), headers=self.headers)
                ).status_code == HTTP_STATUS_OK
        except httpx.RequestError:
            return False
