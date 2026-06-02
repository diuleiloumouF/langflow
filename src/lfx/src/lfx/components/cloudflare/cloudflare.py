# Cloudflare Workers AI 嵌入模型的 LangChain 集成
from langchain_community.embeddings.cloudflare_workersai import CloudflareWorkersAIEmbeddings

# 模型组件基类
from lfx.base.models.model import LCModelComponent

# 嵌入模型类型
from lfx.field_typing import Embeddings

# 输入组件类型
from lfx.io import BoolInput, DictInput, IntInput, MessageTextInput, Output, SecretStrInput


# Cloudflare Workers AI 嵌入组件，用于生成文本嵌入向量
class CloudflareWorkersAIEmbeddingsComponent(LCModelComponent):
    display_name: str = "Cloudflare Workers AI Embeddings"
    description: str = "Generate embeddings using Cloudflare Workers AI models."
    documentation: str = "https://python.langchain.com/docs/integrations/text_embedding/cloudflare_workersai/"
    icon = "Cloudflare"
    name = "CloudflareWorkersAIEmbeddings"

    # 输入参数定义
    inputs = [
        # Cloudflare 账户 ID
        MessageTextInput(
            name="account_id",
            display_name="Cloudflare account ID",
            info="Find your account ID https://developers.cloudflare.com/fundamentals/setup/find-account-and-zone-ids/#find-account-id-workers-and-pages",
            required=True,
        ),
        # Cloudflare API 令牌
        SecretStrInput(
            name="api_token",
            display_name="Cloudflare API token",
            info="Create an API token https://developers.cloudflare.com/fundamentals/api/get-started/create-token/",
            required=True,
        ),
        # 嵌入模型名称
        MessageTextInput(
            name="model_name",
            display_name="Model Name",
            info="List of supported models https://developers.cloudflare.com/workers-ai/models/#text-embeddings",
            required=True,
            value="@cf/baai/bge-base-en-v1.5",
        ),
        # 是否移除换行符
        BoolInput(
            name="strip_new_lines",
            display_name="Strip New Lines",
            advanced=True,
            value=True,
        ),
        # 批处理大小
        IntInput(
            name="batch_size",
            display_name="Batch Size",
            advanced=True,
            value=50,
        ),
        # Cloudflare API 基础 URL
        MessageTextInput(
            name="api_base_url",
            display_name="Cloudflare API base URL",
            advanced=True,
            value="https://api.cloudflare.com/client/v4/accounts",
        ),
        # 额外的请求头
        DictInput(
            name="headers",
            display_name="Headers",
            info="Additional request headers",
            is_list=True,
            advanced=True,
        ),
    ]

    # 输出参数定义
    outputs = [
        Output(display_name="Embeddings", name="embeddings", method="build_embeddings"),
    ]

    # 构建 Cloudflare Workers AI 嵌入模型实例
    def build_embeddings(self) -> Embeddings:
        try:
            embeddings = CloudflareWorkersAIEmbeddings(
                account_id=self.account_id,
                api_base_url=self.api_base_url,
                api_token=self.api_token,
                batch_size=self.batch_size,
                headers=self.headers,
                model_name=self.model_name,
                strip_new_lines=self.strip_new_lines,
            )
        except Exception as e:
            msg = f"Could not connect to CloudflareWorkersAIEmbeddings API: {e!s}"
            raise ValueError(msg) from e

        return embeddings
