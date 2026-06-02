"""Constants, enums, and configuration values for the Watsonx Orchestrate adapter."""
# Watsonx Orchestrate 适配器的常量、枚举和配置值。

from __future__ import annotations

import os
import re
from enum import Enum

from lfx.services.adapters.deployment.schema import DeploymentType

from langflow.services.database.models.deployment_provider_account.schemas import DeploymentProviderKey

# 该适配器支持的部署类型，目前仅支持 AGENT（智能体）类型
SUPPORTED_ADAPTER_DEPLOYMENT_TYPES: frozenset[DeploymentType] = frozenset({DeploymentType.AGENT})

# 创建部署操作的最大重试次数
CREATE_MAX_RETRIES = 3
# 更新部署操作的最大重试次数
UPDATE_MAX_RETRIES = 3
# 回滚操作的最大重试次数
ROLLBACK_MAX_RETRIES = 5
# 重试初始延迟时间（秒）
RETRY_INITIAL_DELAY_SECONDS = 0.5
# 用于清理 Watsonx Orchestrate 名称的正则表达式，只保留字母、数字和下划线
WXO_SANITIZE_RE = re.compile(r"[^a-zA-Z0-9_]")
# 字符替换映射表，将空格和连字符替换为下划线
WXO_TRANSLATE = str.maketrans({" ": "_", "-": "_"})

# 错误消息前缀模板
ERROR_PREFIX = "An error occurred while"
# 错误消息后缀模板
ERROR_SUFFIX_IN = "in Watsonx Orchestrate."

# The IAM endpoints below generate
# authentication tokens for production
# wxO environments and are documented publicly:
# Documentation: https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=api-generating-jwt-aws
# 以下 IAM 端点用于为生产环境生成认证令牌，这些是公开文档化的端点：
# IBM MCSP（Multi-Cloud Service Provider）生产环境的 IAM 认证地址
IBM_IAM_MCSP_PRODUCTION_URL = "https://iam.platform.saas.ibm.com"
# Documentation: https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=api-generating-access-token-cloud
# IBM Cloud 生产环境的 IAM 认证地址
IBM_IAM_PRODUCTION_URL = "https://iam.cloud.ibm.com"
# Non-production wxO environments use different
# IAM URLs, which are not documented publicly
# and must not be used publicly in plain text.
# 非生产环境的 wxO 使用不同的 IAM URL，这些地址未公开文档化，不得以明文形式公开发布。


class WxOAuthURL(str, Enum):
    """IAM token endpoint URLs used to authenticate against Watsonx Orchestrate.

    Non-production wxO environments use a different IAM URL than
    production environments. These cannot be exposed in plain text so
    environment variables are surfaced instead.
    Set ``IBM_IAM_MCSP_DEV_URL_OVERRIDE`` for AWS wxO environments,
    ``IBM_IAM_DEV_URL_OVERRIDE`` for IBM Cloud.
    When unset, the production URLs are used
    ("https://iam.platform.saas.ibm.com" and "https://iam.cloud.ibm.com" respectively).

    Please note:
    - The stated environment variables are solely for
    internal testing and development purposes,
    and must be left unset when shipping Langflow
    for general availability.
    - The IAM URLs cannot be changed during runtime,
    and Langflow does not dynamically resolve the IAM URL based on
    the environment of a given wxO tenant. It simply uses the
    default production IAM URLs, or the environment variable
    overrides if set.
    """

    # 用于 Watsonx Orchestrate 认证的 IAM 令牌端点 URL 枚举。
    # 非生产环境使用与生产环境不同的 IAM URL，这些地址不能以明文形式暴露，因此通过环境变量提供。
    # 设置 IBM_IAM_MCSP_DEV_URL_OVERRIDE 用于 AWS wxO 环境，
    # 设置 IBM_IAM_DEV_URL_OVERRIDE 用于 IBM Cloud。
    # 未设置时使用生产环境 URL。
    # 注意：这些环境变量仅用于内部测试和开发，发布时必须保持未设置状态。

    # MCSP（Multi-Cloud Service Provider）IAM 端点，优先使用环境变量覆盖值，否则使用生产环境 URL
    MCSP = os.getenv("IBM_IAM_MCSP_DEV_URL_OVERRIDE", "").strip() or IBM_IAM_MCSP_PRODUCTION_URL
    # IBM Cloud IAM 端点，优先使用环境变量覆盖值，否则使用生产环境 URL
    IBM_IAM = os.getenv("IBM_IAM_DEV_URL_OVERRIDE", "").strip() or IBM_IAM_PRODUCTION_URL


class ErrorPrefix(str, Enum):
    """部署操作错误消息前缀枚举，用于统一格式化各种部署操作的错误提示信息。"""

    # 创建部署时的错误前缀
    CREATE = f"{ERROR_PREFIX} creating a deployment {ERROR_SUFFIX_IN}"
    # 列出部署时的错误前缀
    LIST = f"{ERROR_PREFIX} listing deployments {ERROR_SUFFIX_IN}"
    # 获取部署详情时的错误前缀
    GET = f"{ERROR_PREFIX} getting a deployment {ERROR_SUFFIX_IN}"
    # 更新部署时的错误前缀
    UPDATE = f"{ERROR_PREFIX} updating a deployment {ERROR_SUFFIX_IN}"
    # 重新部署时的错误前缀
    REDEPLOY = f"{ERROR_PREFIX} redeploying a deployment {ERROR_SUFFIX_IN}"
    # 克隆部署时的错误前缀
    CLONE = f"{ERROR_PREFIX} cloning a deployment {ERROR_SUFFIX_IN}"
    # 删除部署时的错误前缀
    DELETE = f"{ERROR_PREFIX} deleting a deployment {ERROR_SUFFIX_IN}"
    # 获取部署健康状态时的错误前缀
    HEALTH = f"{ERROR_PREFIX} getting a deployment health {ERROR_SUFFIX_IN}"
    # 创建部署配置时的错误前缀
    CREATE_CONFIG = f"{ERROR_PREFIX} creating a deployment config {ERROR_SUFFIX_IN}"
    # 列出部署配置时的错误前缀
    LIST_CONFIGS = f"{ERROR_PREFIX} listing deployment configs {ERROR_SUFFIX_IN}"
    # 获取部署配置时的错误前缀
    GET_CONFIG = f"{ERROR_PREFIX} getting a deployment config {ERROR_SUFFIX_IN}"
    # 更新部署配置时的错误前缀
    UPDATE_CONFIG = f"{ERROR_PREFIX} updating a deployment config {ERROR_SUFFIX_IN}"
    # 删除部署配置时的错误前缀
    DELETE_CONFIG = f"{ERROR_PREFIX} deleting a deployment config {ERROR_SUFFIX_IN}"
    # 列出部署的 LLM 模型时的错误前缀
    LIST_LLMS = f"{ERROR_PREFIX} listing deployment LLMs {ERROR_SUFFIX_IN}"
    # 创建部署执行记录时的错误前缀
    CREATE_EXECUTION = f"{ERROR_PREFIX} creating a deployment execution {ERROR_SUFFIX_IN}"
    # 获取部署执行记录时的错误前缀
    GET_EXECUTION = f"{ERROR_PREFIX} getting a deployment execution {ERROR_SUFFIX_IN}"


WATSONX_ORCHESTRATE_DEPLOYMENT_ADAPTER_KEY = DeploymentProviderKey.WATSONX_ORCHESTRATE.value
