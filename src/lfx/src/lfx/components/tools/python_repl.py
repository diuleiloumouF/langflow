# 动态导入模块工具，用于在运行时根据字符串名称加载模块
import importlib

from langchain_core.tools import StructuredTool, ToolException
from langchain_experimental.utilities import PythonREPL
from pydantic import BaseModel, Field

from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import StrInput
from lfx.log.logger import logger
from lfx.schema.data import Data


# Python REPL 工具组件：在 REPL 环境中执行 Python 代码的 LangChain 工具
# 已标记为 legacy，推荐使用 processing.PythonREPLComponent 替代
class PythonREPLToolComponent(LCToolComponent):
    display_name = "Python REPL"
    description = "A tool for running Python code in a REPL environment."
    name = "PythonREPLTool"
    icon = "Python"
    # 标记为旧版组件，不再维护，提供替代组件列表
    legacy = True
    replacement = ["processing.PythonREPLComponent"]

    # 组件输入参数定义
    inputs = [
        # 工具名称，用于标识该工具
        StrInput(
            name="name",
            display_name="Tool Name",
            info="The name of the tool.",
            value="python_repl",
        ),
        # 工具描述，供 LLM 理解工具用途
        StrInput(
            name="description",
            display_name="Tool Description",
            info="A description of the tool.",
            value="A Python shell. Use this to execute python commands. "
            "Input should be a valid python command. "
            "If you want to see the output of a value, you should print it out with `print(...)`.",
        ),
        # 全局导入的模块列表（逗号分隔），这些模块会在 REPL 环境中全局可用
        StrInput(
            name="global_imports",
            display_name="Global Imports",
            info="A comma-separated list of modules to import globally, e.g. 'math,numpy'.",
            value="math",
        ),
        # 要执行的 Python 代码
        StrInput(
            name="code",
            display_name="Python Code",
            info="The Python code to execute.",
            value="print('Hello, World!')",
        ),
    ]

    class PythonREPLSchema(BaseModel):
        code: str = Field(..., description="The Python code to execute.")

    def get_globals(self, global_imports: str | list[str]) -> dict:
        global_dict = {}
        if isinstance(global_imports, str):
            modules = [module.strip() for module in global_imports.split(",")]
        elif isinstance(global_imports, list):
            modules = global_imports
        else:
            msg = "global_imports must be either a string or a list"
            raise TypeError(msg)

        for module in modules:
            try:
                imported_module = importlib.import_module(module)
                global_dict[imported_module.__name__] = imported_module
            except ImportError as e:
                msg = f"Could not import module {module}"
                raise ImportError(msg) from e
        return global_dict

    def build_tool(self) -> Tool:
        globals_ = self.get_globals(self.global_imports)
        python_repl = PythonREPL(_globals=globals_)

        def run_python_code(code: str) -> str:
            try:
                return python_repl.run(code)
            except Exception as e:
                logger.debug("Error running Python code", exc_info=True)
                raise ToolException(str(e)) from e

        tool = StructuredTool.from_function(
            name=self.name,
            description=self.description,
            func=run_python_code,
            args_schema=self.PythonREPLSchema,
        )

        self.status = f"Python REPL Tool created with global imports: {self.global_imports}"
        return tool

    def run_model(self) -> list[Data]:
        tool = self.build_tool()
        result = tool.run(self.code)
        return [Data(data={"result": result})]
