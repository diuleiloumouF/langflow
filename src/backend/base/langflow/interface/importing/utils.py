# 该模块用于按名称导入任何 langchain 类。
# This module is used to import any langchain class by name.

import importlib
from typing import Any


def import_module(module_path: str) -> Any:
    """Import module from module path."""
    """根据模块路径导入模块。"""
    # 如果模块路径中不包含 "from"，说明是普通的模块导入（如 "langchain.chains"）
    if "from" not in module_path:
        # Import the module using the module path
        import warnings

        with warnings.catch_warnings():
            # 忽略 langchain 中常见的弃用警告和配置变更警告
            warnings.filterwarnings(
                "ignore", message="Support for class-based `config` is deprecated", category=DeprecationWarning
            )
            warnings.filterwarnings("ignore", message="Valid config keys have changed in V2", category=UserWarning)
            return importlib.import_module(module_path)

    # 处理 "from xxx import yyy" 格式的导入语句
    # Split the module path into its components
    _, module_path, _, object_name = module_path.split()

    # Import the module using the module path
    import warnings

    with warnings.catch_warnings():
        # 忽略 langchain 中常见的弃用警告和配置变更警告
        warnings.filterwarnings(
            "ignore", message="Support for class-based `config` is deprecated", category=DeprecationWarning
        )
        warnings.filterwarnings("ignore", message="Valid config keys have changed in V2", category=UserWarning)
        module = importlib.import_module(module_path)

    # 从模块中获取指定的对象（类、函数等）
    return getattr(module, object_name)


def import_class(class_path: str) -> Any:
    """Import class from class path."""
    """根据完整的类路径导入类。

    Args:
        class_path: 完整的类路径，例如 "langchain.chains.LLMChain"。

    Returns:
        导入的类对象。
    """
    # 通过最后一个点号将路径拆分为模块路径和类名
    module_path, class_name = class_path.rsplit(".", 1)
    module = import_module(module_path)
    # 从模块中获取指定的类
    return getattr(module, class_name)
