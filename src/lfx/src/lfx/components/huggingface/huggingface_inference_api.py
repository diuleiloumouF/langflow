from urllib.parse import urlparse

import requests
from langchain_community.embeddings.huggingface import HuggingFaceInferenceAPIEmbeddings

# 下次更新: 使用 langchain_huggingface
# Next update: use langchain_huggingface
from pydantic import SecretStr
from tenacity import retry, stop_after_attempt, wait_fixed

from lfx.base.embeddings.model import LCEmbeddingsModel
from lfx.field_typing import Embeddings
from lfx.io import MessageTextInput, Output, SecretStrInput


# Hugging Face 推理 API 嵌入组件，使用 Hugging Face Text Embeddings Inference (TEI) 生成嵌入向量
# Hugging Face Inference API embeddings component for generating embeddings using TEI
class HuggingFaceInferenceAPIEmbeddingsComponent(LCEmbeddingsModel):
    display_name = "Hugging Face Embeddings Inference"
    description = "Generate embeddings using Hugging Face Text Embeddings Inference (TEI)"
    documentation = "https://huggingface.co/docs/text-embeddings-inference/index"
    icon = "HuggingFace"
    name = "HuggingFaceInferenceAPIEmbeddings"

    inputs = [
        SecretStrInput(
            name="api_key",
            display_name="HuggingFace API Key",
            advanced=False,
            info="Required for non-local inference endpoints. Local inference does not require an API Key.",
        ),
        MessageTextInput(
            name="inference_endpoint",
            display_name="Inference Endpoint",
            required=True,
            value="https://api-inference.huggingface.co/models/",
            info="Custom inference endpoint URL.",
        ),
        MessageTextInput(
            name="model_name",
            display_name="Model Name",
            value="BAAI/bge-large-en-v1.5",
            info="The name of the model to use for text embeddings.",
            required=True,
        ),
    ]

    outputs = [
        Output(display_name="Embeddings", name="embeddings", method="build_embeddings"),
    ]

    # 验证推理端点是否有效且可访问
    def validate_inference_endpoint(self, inference_endpoint: str) -> bool:
        parsed_url = urlparse(inference_endpoint)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            msg = (
                f"Invalid inference endpoint format: '{self.inference_endpoint}'. "
                "Please ensure the URL includes both a scheme (e.g., 'http://' or 'https://') and a domain name. "
                "Example: 'http://localhost:8080' or 'https://api.example.com'"
            )
            raise ValueError(msg)

        try:
            response = requests.get(f"{inference_endpoint}/health", timeout=5)
        except requests.RequestException as e:
            msg = (
                f"Inference endpoint '{inference_endpoint}' is not responding. "
                "Please ensure the URL is correct and the service is running."
            )
            raise ValueError(msg) from e

        if response.status_code != requests.codes.ok:
            msg = f"Hugging Face health check failed: {response.status_code}"
            raise ValueError(msg)
        # returning True to solve linting error
        return True

    # 获取 API URL
    def get_api_url(self) -> str:
        if "huggingface" in self.inference_endpoint.lower():
            return f"{self.inference_endpoint}"
        return self.inference_endpoint

    # 创建 HuggingFace 嵌入实例，支持重试机制（最多3次，每次间隔2秒）
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def create_huggingface_embeddings(
        self, api_key: SecretStr, api_url: str, model_name: str
    ) -> HuggingFaceInferenceAPIEmbeddings:
        return HuggingFaceInferenceAPIEmbeddings(api_key=api_key, api_url=api_url, model_name=model_name)

    # 构建 HuggingFace 嵌入模型实例
    def build_embeddings(self) -> Embeddings:
        api_url = self.get_api_url()

        is_local_url = (
            api_url.startswith(("http://localhost", "http://127.0.0.1", "http://0.0.0.0", "http://docker"))
            or "huggingface.co" not in api_url.lower()
        )

        if not self.api_key and is_local_url:
            self.validate_inference_endpoint(api_url)
            api_key = SecretStr("APIKeyForLocalDeployment")
        elif not self.api_key:
            msg = "API Key is required for non-local inference endpoints"
            raise ValueError(msg)
        else:
            api_key = SecretStr(self.api_key).get_secret_value()

        try:
            return self.create_huggingface_embeddings(api_key, api_url, self.model_name)
        except Exception as e:
            msg = "Could not connect to Hugging Face Inference API."
            raise ValueError(msg) from e
