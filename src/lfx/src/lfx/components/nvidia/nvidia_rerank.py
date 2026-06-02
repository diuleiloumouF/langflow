from typing import Any

from lfx.base.compressors.model import LCCompressorComponent
from lfx.field_typing import BaseDocumentCompressor
from lfx.inputs.inputs import SecretStrInput
from lfx.io import DropdownInput, StrInput
from lfx.schema.dotdict import dotdict
from lfx.template.field.base import Output


# NVIDIA Rerank 组件：使用 NVIDIA API 对文档进行重排序
# 继承自 LCCompressorComponent，提供文档压缩/重排序能力
class NvidiaRerankComponent(LCCompressorComponent):
    display_name = "NVIDIA Rerank"
    description = "Rerank documents using the NVIDIA API."
    icon = "NVIDIA"

    # 组件输入定义：API密钥、基础URL和模型选择
    inputs = [
        *LCCompressorComponent.inputs,
        # NVIDIA API 密钥，用于身份验证
        SecretStrInput(
            name="api_key",
            display_name="NVIDIA API Key",
        ),
        # NVIDIA API 基础地址，支持刷新按钮动态加载可用模型列表
        StrInput(
            name="base_url",
            display_name="Base URL",
            value="https://integrate.api.nvidia.com/v1",
            refresh_button=True,
            info="The base URL of the NVIDIA API. Defaults to https://integrate.api.nvidia.com/v1.",
        ),
        # 重排序模型下拉选择，默认使用 nv-rerank-qa-mistral-4b:1
        DropdownInput(
            name="model",
            display_name="Model",
            options=["nv-rerank-qa-mistral-4b:1"],
            value="nv-rerank-qa-mistral-4b:1",
        ),
    ]

    # 组件输出定义：重排序后的文档列表
    outputs = [
        Output(
            display_name="Reranked Documents",
            name="reranked_documents",
            method="compress_documents",
        ),
    ]

    # 当用户修改 base_url 字段时，动态更新可用模型列表
    def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        if field_name == "base_url" and field_value:
            try:
                # 根据新的 base_url 构建压缩器，获取可用模型列表
                build_model = self.build_compressor()
                ids = [model.id for model in build_model.available_models]
                build_config["model"]["options"] = ids
                build_config["model"]["value"] = ids[0]
            except Exception as e:
                msg = f"Error getting model names: {e}"
                raise ValueError(msg) from e
        return build_config

    # 构建 NVIDIA Rerank 压缩器实例
    def build_compressor(self) -> BaseDocumentCompressor:
        try:
            from langchain_nvidia_ai_endpoints import NVIDIARerank
        except ImportError as e:
            msg = "Please install langchain-nvidia-ai-endpoints to use the NVIDIA model."
            raise ImportError(msg) from e
        return NVIDIARerank(api_key=self.api_key, model=self.model, base_url=self.base_url, top_n=self.top_n)
