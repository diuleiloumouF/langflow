# 服务工厂模块
# 提供服务工厂类和服务类型推断功能，用于动态创建和管理服务实例

import importlib
import inspect
from typing import get_type_hints

from cachetools import LRUCache, cached
from lfx.log.logger import logger

from langflow.services.base import Service
from langflow.services.schema import ServiceType


class ServiceFactory:
    """服务工厂类，用于创建服务实例并管理服务依赖关系"""

    def __init__(
        self,
        service_class: type[Service] | None = None,
    ) -> None:
        # 如果未提供服务类，则抛出 ValueError
        if service_class is None:
            msg = "service_class is required"
            raise ValueError(msg)
        # 保存服务类引用
        self.service_class = service_class
        # 推断并保存该服务的依赖关系
        self.dependencies = infer_service_types(self, import_all_services_into_a_dict())

    def create(self, *args, **kwargs) -> "Service":
        """创建并返回服务实例"""
        return self.service_class(*args, **kwargs)


def hash_factory(factory: ServiceFactory) -> str:
    """计算服务工厂的哈希值，用于缓存键"""
    return factory.service_class.__name__


def hash_dict(d: dict) -> str:
    """计算字典的哈希值，用于缓存键"""
    return str(d)


def hash_infer_service_types_args(factory: ServiceFactory, available_services=None) -> str:
    """计算 infer_service_types 函数参数的哈希值，用于缓存键"""
    factory_hash = hash_factory(factory)
    services_hash = hash_dict(available_services)
    return f"{factory_hash}_{services_hash}"


@cached(cache=LRUCache(maxsize=10), key=hash_infer_service_types_args)
def infer_service_types(factory: ServiceFactory, available_services=None) -> list["ServiceType"]:
    """推断服务工厂所需的服务类型列表"""
    create_method = factory.create

    type_hints = get_type_hints(create_method, globalns=available_services)

    service_types = []
    for param_name, param_type in type_hints.items():
        # 跳过返回类型（如果包含在类型提示中）
        # Skip the return type if it's included in type hints
        if param_name == "return":
            continue

        # 将类型转换为预期的枚举格式，直接使用而不附加 "_SERVICE"
        # Convert the type to the expected enum format directly without appending "_SERVICE"
        type_name = param_type.__name__.upper().replace("SERVICE", "_SERVICE")

        try:
            # 尝试查找匹配的枚举值
            # Attempt to find a matching enum value
            service_type = ServiceType[type_name]
            service_types.append(service_type)
        except KeyError as e:
            msg = f"No matching ServiceType for parameter type: {param_type.__name__}"
            raise ValueError(msg) from e
    return service_types


@cached(cache=LRUCache(maxsize=1))
def import_all_services_into_a_dict():
    """将所有服务模块导入到字典中，用于类型提示解析"""
    # 服务都在 langflow.services.{service_name}.service 中
    # Services are all in langflow.services.{service_name}.service
    # 并且是 Service 的子类
    # and are subclass of Service
    # 我们想导入所有服务并放入字典中
    # We want to import all of them and put them in a dict
    # 用作全局变量
    # to use as globals
    from langflow.services.base import Service

    services = {}
    for service_type in ServiceType:
        try:
            service_name = ServiceType(service_type).value.replace("_service", "")

            # 特殊处理 mcp_composer，它现在位于 lfx 模块中
            # Special handling for mcp_composer which is now in lfx module
            if service_name == "mcp_composer":
                module_name = f"lfx.services.{service_name}.service"
            else:
                module_name = f"langflow.services.{service_name}.service"

            module = importlib.import_module(module_name)
            services.update(
                {
                    name: obj
                    for name, obj in inspect.getmembers(module, inspect.isclass)
                    if isinstance(obj, type) and issubclass(obj, Service) and obj is not Service
                }
            )
        except Exception as exc:
            logger.exception(exc)
            msg = "Could not initialize services. Please check your settings."
            raise RuntimeError(msg) from exc
    # 从 lfx 导入 Settings 和 auth 基类（用于类型提示但不是 langflow Service 子类）
    # Import settings and auth base from lfx (used in type hints but not langflow Service subclasses)
    from lfx.services.auth.base import BaseAuthService
    from lfx.services.settings.service import SettingsService

    services["BaseAuthService"] = BaseAuthService
    services["SettingsService"] = SettingsService
    return services
