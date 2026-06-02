# AST 抽象语法树模块，用于安全解析和求值数学表达式
import ast

# 运算符模块，提供基本算术运算符对应的函数
import operator

import pytest
from langchain_core.tools import ToolException
from pydantic import BaseModel, Field

# 基础 LangChain 工具组件类
from lfx.base.langchain_utilities.model import LCToolComponent

# 工具类型定义
from lfx.field_typing import Tool

# 消息文本输入组件
from lfx.inputs.inputs import MessageTextInput

# 日志记录器
from lfx.log.logger import logger

# 数据模型，用于组件间数据传递
from lfx.schema.data import Data


class CalculatorToolComponent(LCToolComponent):
    """计算器工具组件 - 对给定的数学表达式执行基本算术运算（加减乘除、幂运算）。"""

    # 组件在画布上的显示名称
    display_name = "Calculator"
    # 组件的功能描述
    description = "Perform basic arithmetic operations on a given expression."
    # 组件图标标识
    icon = "calculator"
    # 组件内部唯一名称
    name = "CalculatorTool"
    # 标记为遗留组件，不再推荐使用
    legacy = True
    # 推荐的替代组件
    replacement = ["helpers.CalculatorComponent"]

    # 组件输入参数定义
    inputs = [
        MessageTextInput(
            name="expression",
            display_name="Expression",
            info="The arithmetic expression to evaluate (e.g., '4*4*(33/22)+12-20').",
        ),
    ]

    class CalculatorToolSchema(BaseModel):
        """计算器工具的输入参数 Schema 定义，用于 LangChain StructuredTool。"""

        # 待求值的算术表达式
        expression: str = Field(..., description="The arithmetic expression to evaluate.")

    def run_model(self) -> list[Data]:
        """执行模型运行，解析并计算输入的数学表达式，返回结果数据列表。"""
        return self._evaluate_expression(self.expression)

    def build_tool(self) -> Tool:
        """构建并返回 LangChain StructuredTool 实例，供 Agent 调用。"""
        try:
            from langchain_core.tools import StructuredTool
        except Exception:  # noqa: BLE001
            pytest.skip("langchain is not available")

        return StructuredTool.from_function(
            name="calculator",
            description="Evaluate basic arithmetic expressions. Input should be a string containing the expression.",
            func=self._eval_expr_with_error,
            args_schema=self.CalculatorToolSchema,
        )

    def _eval_expr(self, node):
        # ast.Num was removed in Python 3.14; ast.Constant covers numeric literals since 3.8.
        # 递归求值 AST 节点：处理数值常量、二元运算和一元运算
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            left_val = self._eval_expr(node.left)
            right_val = self._eval_expr(node.right)
            return self.operators[type(node.op)](left_val, right_val)
        if isinstance(node, ast.UnaryOp):
            operand_val = self._eval_expr(node.operand)
            return self.operators[type(node.op)](operand_val)
        if isinstance(node, ast.Call):
            # 不支持函数调用，如 sqrt()、sin()、cos() 等
            msg = (
                "Function calls like sqrt(), sin(), cos() etc. are not supported. "
                "Only basic arithmetic operations (+, -, *, /, **) are allowed."
            )
            raise TypeError(msg)
        # 不支持的节点类型
        msg = f"Unsupported operation or expression type: {type(node).__name__}"
        raise TypeError(msg)

    def _eval_expr_with_error(self, expression: str) -> list[Data]:
        """带错误包装的表达式求值方法，将异常转换为 ToolException 供 LangChain 处理。"""
        try:
            return self._evaluate_expression(expression)
        except Exception as e:
            raise ToolException(str(e)) from e

    def _evaluate_expression(self, expression: str) -> list[Data]:
        """核心表达式求值方法：解析字符串表达式并通过 AST 安全求值，返回结果或错误信息。"""
        try:
            # Parse the expression and evaluate it
            # 使用 AST 解析表达式为语法树，然后递归求值
            tree = ast.parse(expression, mode="eval")
            result = self._eval_expr(tree.body)

            # Format the result to a reasonable number of decimal places
            # 将结果格式化为合理的小数位数，去除末尾多余的零
            formatted_result = f"{result:.6f}".rstrip("0").rstrip(".")

            self.status = formatted_result
            return [Data(data={"result": formatted_result})]

        except (SyntaxError, TypeError, KeyError) as e:
            # 语法错误、类型错误或未知运算符
            error_message = f"Invalid expression: {e}"
            self.status = error_message
            return [Data(data={"error": error_message, "input": expression})]
        except ZeroDivisionError:
            # 除零错误
            error_message = "Error: Division by zero"
            self.status = error_message
            return [Data(data={"error": error_message, "input": expression})]
        except Exception as e:  # noqa: BLE001
            # 其他未预期的异常，记录调试日志
            logger.debug("Error evaluating expression", exc_info=True)
            error_message = f"Error: {e}"
            self.status = error_message
            return [Data(data={"error": error_message, "input": expression})]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # AST 节点类型到 Python 运算符函数的映射表
        self.operators = {
            ast.Add: operator.add,  # 加法
            ast.Sub: operator.sub,  # 减法
            ast.Mult: operator.mul,  # 乘法
            ast.Div: operator.truediv,  # 除法
            ast.Pow: operator.pow,  # 幂运算
        }
