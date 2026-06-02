from typing import Any

from lfx.base.embeddings.model import LCEmbeddingsModel
from lfx.field_typing import Embeddings
from lfx.inputs.inputs import DropdownInput, SecretStrInput
from lfx.io import FloatInput, MessageTextInput
from lfx.schema.dotdict import dotdict


# NVIDIA Embeddings 组件：基于 NVIDIA AI Endpoints 提供文本向量嵌入服务
class NVIDIAEmbeddingsComponent(LCEmbeddingsModel):
    display_name: str = "NVIDIA Embeddings"
    description: str = "Generate embeddings using NVIDIA models."
    icon = "NVIDIA"

    # 组件输入参数定义：模型选择、API 地址、密钥和温度
    inputs = [
        # 嵌入模型下拉选择框，支持 NVIDIA 和 Snowflake 提供的嵌入模型
        DropdownInput(
            name="model",
            display_name="Model",
            options=[
                "nvidia/nv-embed-v1",
                "snowflake/arctic-embed-I",
            ],
            value="nvidia/nv-embed-v1",
            required=True,
        ),
        # NVIDIA API 的基础 URL 地址，可通过刷新按钮自动获取可用模型列表
        MessageTextInput(
            name="base_url",
            display_name="NVIDIA Base URL",
            refresh_button=True,
            value="https://integrate.api.nvidia.com/v1",
            required=True,
        ),
        # NVIDIA API 密钥，用于身份验证
        SecretStrInput(
            name="nvidia_api_key",
            display_name="NVIDIA API Key",
            info="The NVIDIA API Key.",
            advanced=False,
            value="NVIDIA_API_KEY",
            required=True,
        ),
        # 模型生成温度参数，控制输出的随机性
        FloatInput(
            name="temperature",
            display_name="Model Temperature",
            value=0.1,
            advanced=True,
        ),
    ]

    # 当 base_url 字段变更时，动态刷新可用模型列表
    def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        if field_name == "base_url" and field_value:
            try:
                # 构建嵌入实例并获取该 URL 下所有可用模型 ID
                build_model = self.build_embeddings()
                ids = [model.id for model in build_model.available_models]
                build_config["model"]["options"] = ids
                build_config["model"]["value"] = ids[0]
            except Exception as e:
                msg = f"Error getting model names: {e}"
                raise ValueError(msg) from e
        return build_config

    # 构建并返回 NVIDIA Embeddings 实例，供 LangChain 图引擎调用
    def build_embeddings(self) -> Embeddings:
        try:
            from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
        except ImportError as e:
            msg = "Please install langchain-nvidia-ai-endpoints to use the Nvidia model."
            raise ImportError(msg) from e
        try:
            # 使用用户配置的参数创建嵌入模型实例
            output = NVIDIAEmbeddings(
                model=self.model,
                base_url=self.base_url,
                temperature=self.temperature,
                nvidia_api_key=self.nvidia_api_key,
            )
        except Exception as e:
            msg = f"Could not connect to NVIDIA API. Error: {e}"
            raise ValueError(msg) from e
        return output
