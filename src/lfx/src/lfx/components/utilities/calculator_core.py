import ast
import operator
from collections.abc import Callable

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import MessageTextInput
from lfx.io import Output
from lfx.schema.data import Data


# 计算器组件，用于对给定的表达式执行基本的算术运算
class CalculatorComponent(Component):
    # 组件显示名称
    display_name = "Calculator"
    # 组件描述信息
    description = "Perform basic arithmetic operations on a given expression."
    # 组件文档链接
    documentation: str = "https://docs.langflow.org/calculator"
    # 组件图标
    icon = "calculator"

    # Cache operators dictionary as a class variable
    # 运算符映射字典，将 AST 运算符类型映射到实际的运算函数
    OPERATORS: dict[type[ast.operator], Callable] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }

    # 组件输入参数定义
    inputs = [
        MessageTextInput(
            name="expression",
            display_name="Expression",
            info="The arithmetic expression to evaluate (e.g., '4*4*(33/22)+12-20').",
            tool_mode=True,
        ),
    ]

    # 组件输出参数定义
    outputs = [
        Output(display_name="JSON", name="result", type_=Data, method="evaluate_expression"),
    ]

    def _eval_expr(self, node: ast.AST) -> float:
        """Evaluate an AST node recursively."""
        # 递归评估 AST 节点
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int | float):
                return float(node.value)
            error_msg = f"Unsupported constant type: {type(node.value).__name__}"
            raise TypeError(error_msg)

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                error_msg = f"Unsupported binary operator: {op_type.__name__}"
                raise TypeError(error_msg)

            left = self._eval_expr(node.left)
            right = self._eval_expr(node.right)
            return self.OPERATORS[op_type](left, right)

        error_msg = f"Unsupported operation or expression type: {type(node).__name__}"
        raise TypeError(error_msg)

    def evaluate_expression(self) -> Data:
        """Evaluate the mathematical expression and return the result."""
        # 评估数学表达式并返回结果
        try:
            tree = ast.parse(self.expression, mode="eval")
            result = self._eval_expr(tree.body)

            formatted_result = f"{float(result):.6f}".rstrip("0").rstrip(".")
            self.log(f"Calculation result: {formatted_result}")

            self.status = formatted_result
            return Data(data={"result": formatted_result})

        except ZeroDivisionError:
            error_message = "Error: Division by zero"
            self.status = error_message
            return Data(data={"error": error_message, "input": self.expression})

        except (SyntaxError, TypeError, KeyError, ValueError, AttributeError, OverflowError) as e:
            error_message = f"Invalid expression: {e!s}"
            self.status = error_message
            return Data(data={"error": error_message, "input": self.expression})

    def build(self):
        """Return the main evaluation function."""
        # 返回主要的评估函数
        return self.evaluate_expression
