import ast
from typing import Any

from typing_extensions import override


# 必需输入访问器：通过 AST 遍历分析代码，找出组件中实际使用了哪些必需的输入参数
class RequiredInputsVisitor(ast.NodeVisitor):
    def __init__(self, inputs: dict[str, Any]):
        # inputs: 组件的输入参数定义字典，key 为参数名，value 为输入对象（包含 required 属性）
        self.inputs: dict[str, Any] = inputs
        # required_inputs: 收集代码中实际访问到的必需输入参数名集合
        self.required_inputs: set[str] = set()

    # 访问属性节点（如 self.xxx），判断是否引用了必需的输入参数
    @override
    def visit_Attribute(self, node) -> None:
        if (
            # 检查属性的值是否是一个名称节点（ast.Name）
            isinstance(node.value, ast.Name)
            # 检查是否是 self.xxx 形式的访问
            and node.value.id == "self"
            # 检查属性名是否在已定义的输入参数中
            and node.attr in self.inputs
            # 检查该输入参数是否被标记为必需（required）
            and self.inputs[node.attr].required
        ):
            # 将该属性名加入必需输入集合
            self.required_inputs.add(node.attr)
        # 继续递归访问子节点
        self.generic_visit(node)
