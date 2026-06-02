from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lfx.components._importing import import_mod

if TYPE_CHECKING:
    from lfx.components.flow_controls.conditional_router import ConditionalRouterComponent
    from lfx.components.flow_controls.data_conditional_router import DataConditionalRouterComponent
    from lfx.components.flow_controls.flow_tool import FlowToolComponent
    from lfx.components.flow_controls.listen import ListenComponent
    from lfx.components.flow_controls.loop import LoopComponent
    from lfx.components.flow_controls.notify import NotifyComponent
    from lfx.components.flow_controls.pass_message import PassMessageComponent
    from lfx.components.flow_controls.run_flow import RunFlowComponent
    from lfx.components.flow_controls.sub_flow import SubFlowComponent

# 动态导入映射表：组件类名 -> 对应的子模块名称
# 仅在运行时实际访问属性时才进行导入，避免启动时加载所有组件
_dynamic_imports = {
    "ConditionalRouterComponent": "conditional_router",
    "DataConditionalRouterComponent": "data_conditional_router",
    "FlowToolComponent": "flow_tool",
    "ListenComponent": "listen",
    "LoopComponent": "loop",
    "NotifyComponent": "notify",
    "PassMessageComponent": "pass_message",
    "RunFlowComponent": "run_flow",
    "SubFlowComponent": "sub_flow",
}

# 模块公开导出的组件列表，控制 from flow_controls import * 的行为
__all__ = [
    "ConditionalRouterComponent",
    "DataConditionalRouterComponent",
    "FlowToolComponent",
    "ListenComponent",
    "LoopComponent",
    "NotifyComponent",
    "PassMessageComponent",
    "RunFlowComponent",
    "SubFlowComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import flow control components on attribute access."""
    # 仅当访问的属性名在动态导入映射表中时才进行延迟导入
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过 import_mod 按需导入组件模块并返回组件类
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将导入结果缓存到全局命名空间，后续访问不再重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    return list(__all__)
