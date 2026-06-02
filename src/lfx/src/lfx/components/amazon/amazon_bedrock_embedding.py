# 导入 AWS 常量（嵌入模型 ID 和可用区域列表）
from lfx.base.models.aws_constants import AWS_EMBEDDING_MODEL_IDS, AWS_REGIONS

# 导入 LangChain 模型组件基类
from lfx.base.models.model import LCModelComponent

# 导入嵌入类型定义
from lfx.field_typing import Embeddings

# 导入密钥输入组件（用于安全输入 AWS 凭证）
from lfx.inputs.inputs import SecretStrInput

# 导入下拉框输入、消息文本输入和输出组件
from lfx.io import DropdownInput, MessageTextInput, Output


class AmazonBedrockEmbeddingsComponent(LCModelComponent):
    """Amazon Bedrock 嵌入向量组件。

    使用 Amazon Bedrock 服务生成文本嵌入向量。
    支持多种嵌入模型，包括 Titan 等。
    """

    # 组件在界面上显示的名称
    display_name: str = "Amazon Bedrock Embeddings"
    # 组件的功能描述
    description: str = "Generate embeddings using Amazon Bedrock models."
    # 组件图标，使用 Amazon 品牌图标
    icon = "Amazon"
    # 组件内部唯一标识名称
    name = "AmazonBedrockEmbeddings"

    # 组件输入参数定义
    inputs = [
        # 嵌入模型选择下拉框，默认使用 Amazon Titan 嵌入模型 v1
        DropdownInput(
            name="model_id",
            display_name="Model Id",
            options=AWS_EMBEDDING_MODEL_IDS,
            value="amazon.titan-embed-text-v1",
        ),
        # AWS 访问密钥 ID（必填，用于 AWS 身份认证）
        SecretStrInput(
            name="aws_access_key_id",
            display_name="AWS Access Key ID",
            info="The access key for your AWS account."
            "Usually set in Python code as the environment variable 'AWS_ACCESS_KEY_ID'.",
            value="AWS_ACCESS_KEY_ID",
            required=True,
        ),
        # AWS 秘密访问密钥（必填，与访问密钥 ID 配合使用）
        SecretStrInput(
            name="aws_secret_access_key",
            display_name="AWS Secret Access Key",
            info="The secret key for your AWS account. "
            "Usually set in Python code as the environment variable 'AWS_SECRET_ACCESS_KEY'.",
            value="AWS_SECRET_ACCESS_KEY",
            required=True,
        ),
        # AWS 会话令牌（可选，仅临时凭证需要）
        SecretStrInput(
            name="aws_session_token",
            display_name="AWS Session Token",
            advanced=False,
            info="The session key for your AWS account. "
            "Only needed for temporary credentials. "
            "Usually set in Python code as the environment variable 'AWS_SESSION_TOKEN'.",
            value="AWS_SESSION_TOKEN",
        ),
        # AWS 凭证配置文件名称（高级选项，从 ~/.aws/credentials 读取）
        SecretStrInput(
            name="credentials_profile_name",
            display_name="Credentials Profile Name",
            advanced=True,
            info="The name of the profile to use from your "
            "~/.aws/credentials file. "
            "If not provided, the default profile will be used.",
            value="AWS_CREDENTIALS_PROFILE_NAME",
        ),
        # AWS 区域选择下拉框，默认为美东区域
        DropdownInput(
            name="region_name",
            display_name="Region Name",
            value="us-east-1",
            options=AWS_REGIONS,
            info="The AWS region where your Bedrock resources are located.",
        ),
        # 自定义端点 URL（高级选项，用于私有端点或本地测试）
        MessageTextInput(
            name="endpoint_url",
            display_name="Endpoint URL",
            advanced=True,
            info="The URL of the AWS Bedrock endpoint to use.",
        ),
    ]

    # 组件输出定义：输出嵌入向量对象
    outputs = [
        Output(display_name="Embeddings", name="embeddings", method="build_embeddings"),
    ]

    def build_embeddings(self) -> Embeddings:
        """构建并返回 Amazon Bedrock 嵌入向量实例。

        根据提供的 AWS 凭证创建 boto3 会话，
        然后初始化 BedrockEmbeddings 对象用于文本嵌入生成。

        Returns:
            Embeddings: 配置好的 Bedrock 嵌入向量实例。

        Raises:
            ImportError: 如果 langchain_aws 或 boto3 未安装。
        """
        # 延迟导入 langchain_aws 库（按需加载，避免不必要的依赖）
        try:
            from langchain_aws import BedrockEmbeddings
        except ImportError as e:
            msg = "langchain_aws is not installed. Please install it with `pip install langchain_aws`."
            raise ImportError(msg) from e
        # 延迟导入 boto3 库（AWS SDK for Python）
        try:
            import boto3
        except ImportError as e:
            msg = "boto3 is not installed. Please install it with `pip install boto3`."
            raise ImportError(msg) from e

        # 根据凭证配置创建 boto3 会话
        # 优先使用显式提供的访问密钥
        if self.aws_access_key_id or self.aws_secret_access_key:
            session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_session_token=self.aws_session_token,
            )
        # 其次使用凭证配置文件名称
        elif self.credentials_profile_name:
            session = boto3.Session(profile_name=self.credentials_profile_name)
        # 最后使用默认凭证链（环境变量、实例配置等）
        else:
            session = boto3.Session()

        # 构建 Bedrock 客户端参数
        client_params = {}
        # 如果指定了自定义端点 URL，则添加到客户端参数中
        if self.endpoint_url:
            client_params["endpoint_url"] = self.endpoint_url
        # 如果指定了区域，则添加到客户端参数中
        if self.region_name:
            client_params["region_name"] = self.region_name

        # 创建 Bedrock Runtime 客户端
        boto3_client = session.client("bedrock-runtime", **client_params)
        # 返回配置好的嵌入向量实例
        return BedrockEmbeddings(
            credentials_profile_name=self.credentials_profile_name,
            client=boto3_client,
            model_id=self.model_id,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
        )
