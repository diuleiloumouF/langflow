from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, DropdownInput, MessageTextInput, Output
from lfx.schema.data import Data
from lfx.schema.dotdict import dotdict


class DataConditionalRouterComponent(Component):
    """数据条件路由器组件：根据指定键的条件值将 Data 对象路由到不同的输出端口。

    支持多种比较运算符和布尔值校验。
    """

    # 组件在画布上显示的名称
    display_name = "Condition"
    # 组件的功能描述
    description = "Route Data object(s) based on a condition applied to a specified key, including boolean validation."
    # 画布上显示的图标
    icon = "split"
    # 组件的唯一标识名称
    name = "DataConditionalRouter"
    # 标记为遗留组件，不再推荐使用
    legacy = True
    # 推荐的替代组件
    replacement = ["logic.ConditionalRouter"]

    # 组件的输入参数定义
    inputs = [
        DataInput(
            name="data_input",
            display_name="Data Input",
            # 要处理的 Data 对象或 Data 对象列表
            info="The Data object or list of Data objects to process",
            is_list=True,
        ),
        MessageTextInput(
            name="key_name",
            display_name="Key Name",
            # 要检查的 Data 对象中的键名
            info="The name of the key in the Data object(s) to check",
        ),
        DropdownInput(
            name="operator",
            display_name="Operator",
            # 可选的比较运算符列表，boolean validator 将值作为布尔值处理
            options=["equals", "not equals", "contains", "starts with", "ends with", "boolean validator"],
            info="The operator to apply for comparing the values. 'boolean validator' treats the value as a boolean.",
            value="equals",
        ),
        MessageTextInput(
            name="compare_value",
            display_name="Match Text",
            # 用于比较的目标值，布尔校验模式下不使用此参数
            info="The value to compare against (not used for boolean validator)",
        ),
    ]

    # 组件的输出端口定义
    outputs = [
        # 条件为真时的输出端口
        Output(display_name="True Output", name="true_output", method="process_data"),
        # 条件为假时的输出端口
        Output(display_name="False Output", name="false_output", method="process_data"),
    ]

    def compare_values(self, item_value: str, compare_value: str, operator: str) -> bool:
        """根据指定的运算符比较两个值，返回比较结果。"""
        if operator == "equals":
            return item_value == compare_value
        if operator == "not equals":
            return item_value != compare_value
        if operator == "contains":
            return compare_value in item_value
        if operator == "starts with":
            return item_value.startswith(compare_value)
        if operator == "ends with":
            return item_value.endswith(compare_value)
        if operator == "boolean validator":
            return self.parse_boolean(item_value)
        return False

    def parse_boolean(self, value):
        """将各种类型的值解析为布尔值。

        支持 bool 类型直接返回，字符串类型识别 'true'/'1'/'yes'/'y'/'on'。
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"true", "1", "yes", "y", "on"}
        return bool(value)

    def validate_input(self, data_item: Data) -> bool:
        """校验输入数据：检查是否为 Data 对象，以及指定的键名是否存在于数据中。"""
        if not isinstance(data_item, Data):
            self.status = "Input is not a Data object"
            return False
        if self.key_name not in data_item.data:
            self.status = f"Key '{self.key_name}' not found in Data"
            return False
        return True

    def process_data(self) -> Data | list[Data]:
        """主处理方法：根据条件将输入数据分流到 true_output 或 false_output 端口。

        支持单个 Data 对象和 Data 对象列表两种输入模式。
        """
        if isinstance(self.data_input, list):
            # 列表模式：逐个处理每个 Data 对象并分流
            true_output = []
            false_output = []
            for item in self.data_input:
                if self.validate_input(item):
                    result = self.process_single_data(item)
                    if result:
                        true_output.append(item)
                    else:
                        false_output.append(item)
            # 如果有 true 结果则停止 false 端口，反之亦然
            self.stop("false_output" if true_output else "true_output")
            return true_output or false_output
        # 单对象模式：校验并处理单个 Data 对象
        if not self.validate_input(self.data_input):
            return Data(data={"error": self.status})
        result = self.process_single_data(self.data_input)
        self.stop("false_output" if result else "true_output")
        return self.data_input

    def process_single_data(self, data_item: Data) -> bool:
        """处理单个 Data 对象的条件判断逻辑，返回条件是否满足。"""
        item_value = data_item.data[self.key_name]
        operator = self.operator

        if operator == "boolean validator":
            # 布尔校验模式：直接将值作为布尔值解析
            condition_met = self.parse_boolean(item_value)
            condition_description = f"Boolean validation of '{self.key_name}'"
        else:
            # 比较模式：使用指定运算符进行字符串比较
            compare_value = self.compare_value
            condition_met = self.compare_values(str(item_value), compare_value, operator)
            condition_description = f"{self.key_name} {operator} {compare_value}"

        if condition_met:
            self.status = f"Condition met: {condition_description}"
            return True
        self.status = f"Condition not met: {condition_description}"
        return False

    def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        """动态更新组件的构建配置：当运算符切换为布尔校验时，隐藏匹配文本输入框。"""
        if field_name == "operator":
            if field_value == "boolean validator":
                # 布尔校验模式下隐藏 compare_value 输入框
                build_config["compare_value"]["show"] = False
                build_config["compare_value"]["advanced"] = True
                build_config["compare_value"]["value"] = None
            else:
                # 其他运算符模式下显示 compare_value 输入框
                build_config["compare_value"]["show"] = True
                build_config["compare_value"]["advanced"] = False

        return build_config
