from lfx.base.models.aws_constants import AWS_REGIONS, AWS_MODEL_IDs
from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.inputs.inputs import MessageTextInput, SecretStrInput
from lfx.io import DictInput, DropdownInput


# Amazon Bedrock 模型组件（已废弃，推荐使用 AmazonBedrockConverseModel）
class AmazonBedrockComponent(LCModelComponent):
    # 显示名称
    display_name: str = "Amazon Bedrock"
    # 组件描述信息
    description: str = (
        "Generate text using Amazon Bedrock LLMs with the legacy ChatBedrock API. "
        "This component is deprecated. Please use Amazon Bedrock Converse instead "
        "for better compatibility, newer features, and improved conversation handling."
    )
    # 组件图标
    icon = "Amazon"
    # 组件内部名称
    name = "AmazonBedrockModel"
    # 标记为废弃组件
    legacy = True
    # 推荐使用的替代组件
    replacement = "amazon.AmazonBedrockConverseModel"

    # 组件输入参数定义列表
    inputs = [
        # 继承基础模型组件的输入参数
        *LCModelComponent.get_base_inputs(),
        # 模型 ID 下拉选择，支持所有可用的 Bedrock 模型
        DropdownInput(
            name="model_id",
            display_name="Model ID",
            options=AWS_MODEL_IDs,
            value="anthropic.claude-3-haiku-20240307-v1:0",
            info="List of available model IDs to choose from.",
        ),
        # AWS 访问密钥 ID，用于身份认证
        SecretStrInput(
            name="aws_access_key_id",
            display_name="AWS Access Key ID",
            info="The access key for your AWS account."
            "Usually set in Python code as the environment variable 'AWS_ACCESS_KEY_ID'.",
            value="AWS_ACCESS_KEY_ID",
            required=True,
        ),
        # AWS 私密访问密钥，用于身份认证
        SecretStrInput(
            name="aws_secret_access_key",
            display_name="AWS Secret Access Key",
            info="The secret key for your AWS account. "
            "Usually set in Python code as the environment variable 'AWS_SECRET_ACCESS_KEY'.",
            value="AWS_SECRET_ACCESS_KEY",
            required=True,
        ),
        # AWS 会话令牌，仅用于临时凭证场景
        SecretStrInput(
            name="aws_session_token",
            display_name="AWS Session Token",
            advanced=False,
            info="The session key for your AWS account. "
            "Only needed for temporary credentials. "
            "Usually set in Python code as the environment variable 'AWS_SESSION_TOKEN'.",
            load_from_db=False,
        ),
        # AWS 凭证配置文件名，从 ~/.aws/credentials 中读取指定 profile
        SecretStrInput(
            name="credentials_profile_name",
            display_name="Credentials Profile Name",
            advanced=True,
            info="The name of the profile to use from your "
            "~/.aws/credentials file. "
            "If not provided, the default profile will be used.",
            load_from_db=False,
        ),
        # AWS 区域名称，Bedrock 服务所在区域
        DropdownInput(
            name="region_name",
            display_name="Region Name",
            value="us-east-1",
            options=AWS_REGIONS,
            info="The AWS region where your Bedrock resources are located.",
        ),
        # 模型额外参数，以键值对形式传递给模型
        DictInput(
            name="model_kwargs",
            display_name="Model Kwargs",
            advanced=True,
            is_list=True,
            info="Additional keyword arguments to pass to the model.",
        ),
        # Bedrock 端点 URL，用于自定义端点或私有部署
        MessageTextInput(
            name="endpoint_url",
            display_name="Endpoint URL",
            advanced=True,
            info="The URL of the Bedrock endpoint to use.",
        ),
    ]

    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        # 构建并返回 LangChain ChatBedrock 模型实例
        try:
            from langchain_aws import ChatBedrock
        except ImportError as e:
            msg = "langchain_aws is not installed. Please install it with `pip install langchain_aws`."
            raise ImportError(msg) from e
        try:
            import boto3
        except ImportError as e:
            msg = "boto3 is not installed. Please install it with `pip install boto3`."
            raise ImportError(msg) from e
        # 根据凭证信息创建 boto3 会话
        if self.aws_access_key_id or self.aws_secret_access_key:
            # 使用显式提供的访问密钥创建会话
            try:
                session = boto3.Session(
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    aws_session_token=self.aws_session_token,
                )
            except Exception as e:
                msg = "Could not create a boto3 session."
                raise ValueError(msg) from e
        elif self.credentials_profile_name:
            # 使用指定的 AWS 配置文件创建会话
            session = boto3.Session(profile_name=self.credentials_profile_name)
        else:
            # 使用默认凭证链创建会话
            session = boto3.Session()

        # 构建 Bedrock Runtime 客户端参数
        client_params = {}
        if self.endpoint_url:
            client_params["endpoint_url"] = self.endpoint_url
        if self.region_name:
            client_params["region_name"] = self.region_name

        # 创建 Bedrock Runtime 客户端
        boto3_client = session.client("bedrock-runtime", **client_params)
        try:
            # 初始化 ChatBedrock 模型实例
            output = ChatBedrock(
                client=boto3_client,
                model_id=self.model_id,
                region_name=self.region_name,
                model_kwargs=self.model_kwargs,
                endpoint_url=self.endpoint_url,
                streaming=self.stream,
            )
        except Exception as e:
            msg = "Could not connect to AmazonBedrock API."
            raise ValueError(msg) from e
        return output
