"""Watsonx Orchestrate deployment adapter."""
# Watsonx Orchestrate 部署适配器模块。

from lfx.services.adapters.registry import register_adapter

# register_adapter: 将适配器注册到全局适配器注册表中，以便根据类型和键值查找。
from lfx.services.adapters.schema import AdapterType

# AdapterType: 定义适配器类型的枚举（如 DEPLOYMENT、MODEL 等）。
from langflow.services.adapters.deployment.watsonx_orchestrate.constants import (
    WATSONX_ORCHESTRATE_DEPLOYMENT_ADAPTER_KEY,
)

# WATSONX_ORCHESTRATE_DEPLOYMENT_ADAPTER_KEY: Watsonx Orchestrate 部署适配器的唯一标识键。
from langflow.services.adapters.deployment.watsonx_orchestrate.service import WatsonxOrchestrateDeploymentService

# WatsonxOrchestrateDeploymentService: Watsonx Orchestrate 部署服务的核心实现类，
# 继承自 BaseDeploymentService，负责 agent 的创建、更新、删除、列表查询等操作。
from langflow.services.adapters.deployment.watsonx_orchestrate.types import WxOCredentials

# WxOCredentials: 存储 Watsonx Orchestrate 的实例 URL 和认证信息的数据类。

# 使用装饰器将 WatsonxOrchestrateDeploymentService 注册为 DEPLOYMENT 类型的适配器。
# 注册后，系统可根据适配器类型和键值自动发现并加载该服务。
register_adapter(
    AdapterType.DEPLOYMENT,
    WATSONX_ORCHESTRATE_DEPLOYMENT_ADAPTER_KEY,
)(WatsonxOrchestrateDeploymentService)

# 模块公开的 API 列表，控制 from module import * 的行为。
__all__ = [
    "WatsonxOrchestrateDeploymentService",  # 部署服务主类
    "WxOCredentials",  # 凭据数据类
]
