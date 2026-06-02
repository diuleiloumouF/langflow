from collections.abc import Callable

from lfx.custom.custom_component.component import Component
from lfx.custom.utils import get_function
from lfx.io import CodeInput, Output
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.dotdict import dotdict
from lfx.schema.message import Message


# Python 函数组件，允许用户定义和执行 Python 函数，返回 Data 对象或 Message
class PythonFunctionComponent(Component):
    # 组件显示名称
    display_name = "Python Function"
    # 组件描述信息
    description = "Define and execute a Python function that returns a Data object or a Message."
    # 组件图标
    icon = "Python"
    # 组件内部名称
    name = "PythonFunction"
    # 标记为遗留组件
    legacy = True

    # 组件输入参数定义
    inputs = [
        CodeInput(
            name="function_code",
            display_name="Function Code",
            info="The code for the function.",
        ),
    ]

    # 组件输出参数定义
    outputs = [
        Output(
            name="function_output",
            display_name="Function Callable",
            method="get_function_callable",
        ),
        Output(
            name="function_output_data",
            display_name="Function Output (JSON)",
            method="execute_function_data",
        ),
        Output(
            name="function_output_str",
            display_name="Function Output (Message)",
            method="execute_function_message",
        ),
    ]

    # 获取函数的可调用对象
    def get_function_callable(self) -> Callable:
        function_code = self.function_code
        self.status = function_code
        return get_function(function_code)

    # 执行函数并返回结果
    def execute_function(self) -> list[dotdict | str] | dotdict | str:
        function_code = self.function_code

        if not function_code:
            return "No function code provided."

        try:
            func = get_function(function_code)
            return func()
        except Exception as e:  # noqa: BLE001
            logger.debug("Error executing function", exc_info=True)
            return f"Error executing function: {e}"

    # 执行函数并返回 Data 对象列表
    def execute_function_data(self) -> list[Data]:
        results = self.execute_function()
        results = results if isinstance(results, list) else [results]
        return [(Data(text=x) if isinstance(x, str) else Data(**x)) for x in results]

    # 执行函数并返回 Message 对象
    def execute_function_message(self) -> Message:
        results = self.execute_function()
        results = results if isinstance(results, list) else [results]
        results_list = [str(x) for x in results]
        results_str = "\n".join(results_list)
        return Message(text=results_str)
