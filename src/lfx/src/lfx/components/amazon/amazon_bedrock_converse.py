# 导入语言模型类型定义
from langflow.field_typing import LanguageModel

# 导入各种输入组件类型
from langflow.inputs.inputs import BoolInput, FloatInput, IntInput, MessageTextInput, SecretStrInput

# 导入字典输入和下拉选择输入组件
from langflow.io import DictInput, DropdownInput

# 导入 AWS 常量：区域列表和模型 ID 列表
from lfx.base.models.aws_constants import AWS_REGIONS, AWS_MODEL_IDs

# 导入 LangChain 模型基类
from lfx.base.models.model import LCModelComponent


# Amazon Bedrock Converse 组件
# 使用 Amazon Bedrock 的现代 Converse API 生成文本，提供改进的对话处理能力
class AmazonBedrockConverseComponent(LCModelComponent):
    display_name: str = "Amazon Bedrock Converse"
    # 组件描述：使用 Amazon Bedrock LLM 的现代 Converse API 生成文本，提供改进的对话处理能力
    description: str = (
        "Generate text using Amazon Bedrock LLMs with the modern Converse API for improved conversation handling."
    )
    icon = "Amazon"
    name = "AmazonBedrockConverseModel"
    beta = True

    # 组件输入定义
    inputs = [
        # 继承基础模型组件的所有输入（如 system message 等）
        *LCModelComponent.get_base_inputs(),
        # 模型 ID 下拉选择框
        DropdownInput(
            name="model_id",
            display_name="Model ID",
            options=AWS_MODEL_IDs,
            value="anthropic.claude-3-5-sonnet-20241022-v2:0",
            # 可用模型 ID 列表
            info="List of available model IDs to choose from.",
        ),
        # AWS 访问密钥 ID（必需）
        SecretStrInput(
            name="aws_access_key_id",
            display_name="AWS Access Key ID",
            # AWS 账户的访问密钥，通常通过环境变量 'AWS_ACCESS_KEY_ID' 设置
            info="The access key for your AWS account. "
            "Usually set in Python code as the environment variable 'AWS_ACCESS_KEY_ID'.",
            value="AWS_ACCESS_KEY_ID",
            required=True,
        ),
        # AWS 秘密访问密钥（必需）
        SecretStrInput(
            name="aws_secret_access_key",
            display_name="AWS Secret Access Key",
            # AWS 账户的秘密密钥，通常通过环境变量 'AWS_SECRET_ACCESS_KEY' 设置
            info="The secret key for your AWS account. "
            "Usually set in Python code as the environment variable 'AWS_SECRET_ACCESS_KEY'.",
            value="AWS_SECRET_ACCESS_KEY",
            required=True,
        ),
        # AWS 会话令牌（可选，用于临时凭证）
        SecretStrInput(
            name="aws_session_token",
            display_name="AWS Session Token",
            advanced=True,
            # AWS 账户的会话密钥，仅临时凭证需要，通常通过环境变量 'AWS_SESSION_TOKEN' 设置
            info="The session key for your AWS account. "
            "Only needed for temporary credentials. "
            "Usually set in Python code as the environment variable 'AWS_SESSION_TOKEN'.",
            load_from_db=False,
        ),
        # AWS 凭证配置文件名称（可选）
        SecretStrInput(
            name="credentials_profile_name",
            display_name="Credentials Profile Name",
            advanced=True,
            # 要使用的 ~/.aws/credentials 文件中的配置文件名称，未提供则使用默认配置
            info="The name of the profile to use from your "
            "~/.aws/credentials file. "
            "If not provided, the default profile will be used.",
            load_from_db=False,
        ),
        # AWS 区域选择
        DropdownInput(
            name="region_name",
            display_name="Region Name",
            value="us-east-1",
            options=AWS_REGIONS,
            # Bedrock 资源所在的 AWS 区域
            info="The AWS region where your Bedrock resources are located.",
        ),
        # Bedrock 端点 URL（可选，用于自定义端点）
        MessageTextInput(
            name="endpoint_url",
            display_name="Endpoint URL",
            advanced=True,
            info="The URL of the Bedrock endpoint to use.",
        ),
        # 模型特定参数，用于精细控制
        # Model-specific parameters for fine control
        # 温度参数：控制输出的随机性，值越高输出越随机
        FloatInput(
            name="temperature",
            display_name="Temperature",
            value=0.7,
            # 控制输出的随机性，较高的值使输出更加随机
            info="Controls randomness in output. Higher values make output more random.",
            advanced=True,
        ),
        # 最大 token 数
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            value=4096,
            # 要生成的最大 token 数量
            info="Maximum number of tokens to generate.",
            advanced=True,
        ),
        # Top P 参数：核采样参数，控制输出的多样性
        FloatInput(
            name="top_p",
            display_name="Top P",
            value=0.9,
            # 核采样参数，控制输出的多样性
            info="Nucleus sampling parameter. Controls diversity of output.",
            advanced=True,
        ),
        # Top K 参数：限制考虑的最高概率词汇 token 数量
        IntInput(
            name="top_k",
            display_name="Top K",
            value=250,
            # 限制考虑的最高概率词汇 token 数量，并非所有模型都支持 top_k
            info="Limits the number of highest probability vocabulary tokens to consider. "
            "Note: Not all models support top_k. Use 'Additional Model Fields' for manual configuration if needed.",
            advanced=True,
        ),
        # 禁用流式响应开关
        BoolInput(
            name="disable_streaming",
            display_name="Disable Streaming",
            value=False,
            # 如果为 True，禁用流式响应，适用于批处理场景
            info="If True, disables streaming responses. Useful for batch processing.",
            advanced=True,
        ),
        # 附加模型字段（键值对列表）
        DictInput(
            name="additional_model_fields",
            display_name="Additional Model Fields",
            advanced=True,
            is_list=True,
            # 额外的模型特定参数，用于微调行为
            info="Additional model-specific parameters for fine-tuning behavior.",
        ),
    ]

    # 构建 ChatBedrockConverse 模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        # 动态导入 langchain_aws 库，如果未安装则抛出 ImportError
        try:
            from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse
        except ImportError as e:
            msg = "langchain_aws is not installed. Please install it with `pip install langchain_aws`."
            raise ImportError(msg) from e

        # 准备初始化参数
        # Prepare initialization parameters
        init_params = {
            "model": self.model_id,
            "region_name": self.region_name,
        }

        # 如果提供了 AWS 凭证，则添加到初始化参数中
        # Add AWS credentials if provided
        if self.aws_access_key_id:
            init_params["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            init_params["aws_secret_access_key"] = self.aws_secret_access_key
        if self.aws_session_token:
            init_params["aws_session_token"] = self.aws_session_token
        if self.credentials_profile_name:
            init_params["credentials_profile_name"] = self.credentials_profile_name
        if self.endpoint_url:
            init_params["endpoint_url"] = self.endpoint_url

        # 添加 ChatBedrockConverse 支持的模型参数
        # Add model parameters directly as supported by ChatBedrockConverse
        if hasattr(self, "temperature") and self.temperature is not None:
            init_params["temperature"] = self.temperature
        if hasattr(self, "max_tokens") and self.max_tokens is not None:
            init_params["max_tokens"] = self.max_tokens
        if hasattr(self, "top_p") and self.top_p is not None:
            init_params["top_p"] = self.top_p

        # 处理流式响应设置——仅在明确请求时禁用
        # Handle streaming - only disable if explicitly requested
        if hasattr(self, "disable_streaming") and self.disable_streaming:
            init_params["disable_streaming"] = True

        # 谨慎处理附加模型请求字段
        # 根据错误信息，某些模型不应将 inferenceConfig 作为附加字段传递
        # Handle additional model request fields carefully
        # Based on the error, inferenceConfig should not be passed as additional fields for some models
        additional_model_request_fields = {}

        # 仅在用户明确提供了附加字段或特定模型需要时才添加 top_k
        # Only add top_k if user explicitly provided additional fields or if needed for specific models
        if hasattr(self, "additional_model_fields") and self.additional_model_fields:
            for field in self.additional_model_fields:
                if isinstance(field, dict):
                    additional_model_request_fields.update(field)

        # 目前不自动添加 inferenceConfig 的 top_k，以避免验证错误
        # 用户可以通过 additional_model_fields 手动添加（如果其模型支持）
        # For now, don't automatically add inferenceConfig for top_k to avoid validation errors
        # Users can manually add it via additional_model_fields if their model supports it

        # 仅在有实际附加字段时才添加
        # Only add if we have actual additional fields
        if additional_model_request_fields:
            init_params["additional_model_request_fields"] = additional_model_request_fields

        try:
            # 创建 ChatBedrockConverse 实例
            output = ChatBedrockConverse(**init_params)
        except Exception as e:
            # 提供有用的错误信息和回退建议
            # Provide helpful error message with fallback suggestions
            error_details = str(e)
            if "validation error" in error_details.lower():
                # 验证错误：可能是模型参数不兼容
                msg = (
                    f"ChatBedrockConverse validation error: {error_details}. "
                    f"This may be due to incompatible parameters for model '{self.model_id}'. "
                    f"Consider adjusting the model parameters or trying the legacy Amazon Bedrock component."
                )
            elif "converse api" in error_details.lower():
                # Converse API 错误：模型可能不支持 Converse API
                msg = (
                    f"Converse API error: {error_details}. "
                    f"The model '{self.model_id}' may not support the Converse API. "
                    f"Try using the legacy Amazon Bedrock component instead."
                )
            else:
                msg = f"Could not initialize ChatBedrockConverse: {error_details}"
            raise ValueError(msg) from e

        # 返回构建好的 ChatBedrockConverse 模型实例
        return output
