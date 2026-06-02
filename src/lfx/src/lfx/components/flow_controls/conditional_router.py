import re

from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, DropdownInput, IntInput, MessageInput, MessageTextInput, Output
from lfx.schema.message import Message


class ConditionalRouterComponent(Component):
    """条件路由组件，根据文本比较结果将输入消息路由到对应的输出分支。"""

    display_name = "If-Else"
    description = "Routes an input message to a corresponding output based on text comparison."
    documentation: str = "https://docs.langflow.org/if-else"
    icon = "split"
    name = "ConditionalRouter"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 标记当前迭代是否已更新，防止同一次执行中重复递增迭代计数
        self.__iteration_updated = False

    # 组件输入定义
    inputs = [
        # 主文本输入，用于与匹配文本进行比较
        MessageTextInput(
            name="input_text",
            display_name="Text Input",
            info="The primary text input for the operation.",
            required=True,
        ),
        # 比较运算符选择，支持等于、不等于、包含、正则等多种比较方式
        DropdownInput(
            name="operator",
            display_name="Operator",
            options=[
                "equals",
                "not equals",
                "contains",
                "starts with",
                "ends with",
                "regex",
                "less than",
                "less than or equal",
                "greater than",
                "greater than or equal",
            ],
            info="The operator to apply for comparing the texts.",
            value="equals",
            real_time_refresh=True,
        ),
        # 匹配文本输入，与主文本进行比较的目标文本
        MessageTextInput(
            name="match_text",
            display_name="Match Text",
            info="The text input to compare against.",
            required=True,
        ),
        # 是否区分大小写，正则模式下该选项不生效
        BoolInput(
            name="case_sensitive",
            display_name="Case Sensitive",
            info="If true, the comparison will be case sensitive.",
            value=True,
            advanced=True,
        ),
        # 条件为真时传递的消息
        MessageInput(
            name="true_case_message",
            display_name="Case True",
            info="The message to pass if the condition is True.",
            advanced=True,
        ),
        # 条件为假时传递的消息
        MessageInput(
            name="false_case_message",
            display_name="Case False",
            info="The message to pass if the condition is False.",
            advanced=True,
        ),
        # 最大迭代次数，防止条件路由形成无限循环
        IntInput(
            name="max_iterations",
            display_name="Max Iterations",
            info="The maximum number of iterations for the conditional router.",
            value=10,
            advanced=True,
        ),
        # 达到最大迭代次数时的默认路由方向
        DropdownInput(
            name="default_route",
            display_name="Default Route",
            options=["true_result", "false_result"],
            info="The default route to take when max iterations are reached.",
            value="false_result",
            advanced=True,
        ),
    ]

    # 组件输出定义：True 和 False 两个分支
    outputs = [
        Output(display_name="True", name="true_result", method="true_response", group_outputs=True),
        Output(display_name="False", name="false_result", method="false_response", group_outputs=True),
    ]

    def _pre_run_setup(self):
        """每次执行前重置迭代更新标记。"""
        self.__iteration_updated = False

    def evaluate_condition(self, input_text: str, match_text: str, operator: str, *, case_sensitive: bool) -> bool:
        """根据指定的运算符对两个文本进行比较，返回比较结果。"""
        # 非正则模式下，根据大小写敏感设置统一转换文本
        if not case_sensitive and operator != "regex":
            input_text = input_text.lower()
            match_text = match_text.lower()

        # 等于比较
        if operator == "equals":
            return input_text == match_text
        # 不等于比较
        if operator == "not equals":
            return input_text != match_text
        # 包含比较：检查 match_text 是否在 input_text 中
        if operator == "contains":
            return match_text in input_text
        # 前缀比较
        if operator == "starts with":
            return input_text.startswith(match_text)
        # 后缀比较
        if operator == "ends with":
            return input_text.endswith(match_text)
        # 正则匹配：使用 match_text 作为正则表达式匹配 input_text
        if operator == "regex":
            try:
                return bool(re.match(match_text, input_text))
            except re.error:
                return False  # Return False if the regex is invalid
        # 数值比较：将文本转换为浮点数后进行大小比较
        if operator in ["less than", "less than or equal", "greater than", "greater than or equal"]:
            try:
                input_num = float(input_text)
                match_num = float(match_text)
                if operator == "less than":
                    return input_num < match_num
                if operator == "less than or equal":
                    return input_num <= match_num
                if operator == "greater than":
                    return input_num > match_num
                if operator == "greater than or equal":
                    return input_num >= match_num
            except ValueError:
                return False  # Invalid number format for comparison
        return False

    def iterate_and_stop_once(self, route_to_stop: str):
        """处理循环迭代计数和分支排除。

        使用两种互补机制：
        1. stop() - 用于循环管理的 ACTIVE/INACTIVE 状态（每次迭代重置）
        2. exclude_branch_conditionally() - 用于条件路由的持久排除

        当达到最大迭代次数时，通过允许 default_route 执行来打破循环。
        """
        if not self.__iteration_updated:
            # 递增迭代计数器，确保每次执行只递增一次
            self.update_ctx({f"{self._id}_iteration": self.ctx.get(f"{self._id}_iteration", 0) + 1})
            self.__iteration_updated = True
            current_iteration = self.ctx.get(f"{self._id}_iteration", 0)

            # Check if max iterations reached and we're trying to stop the default route
            # 达到最大迭代次数且尝试停止默认路由时，强制切换到默认路由以打破循环
            if current_iteration >= self.max_iterations and route_to_stop == self.default_route:
                # Clear ALL conditional exclusions to allow default route to execute
                # 清除所有条件排除，允许默认路由执行
                if self._id in self.graph.conditional_exclusion_sources:
                    previous_exclusions = self.graph.conditional_exclusion_sources[self._id]
                    self.graph.conditionally_excluded_vertices -= previous_exclusions
                    del self.graph.conditional_exclusion_sources[self._id]

                # Switch which route to stop - stop the NON-default route to break the cycle
                # 切换要停止的路由方向，停止非默认路由以打破循环
                route_to_stop = "true_result" if route_to_stop == "false_result" else "false_result"

                # Call stop to break the cycle
                self.stop(route_to_stop)
                # Don't apply conditional exclusion when breaking cycle
                return

            # Normal case: Use BOTH mechanisms
            # 正常情况：同时使用两种机制
            # 1. stop() for cycle management (marks INACTIVE, updates run manager, gets reset)
            # stop() 用于循环管理（标记为 INACTIVE，更新运行管理器，每次迭代重置）
            self.stop(route_to_stop)

            # 2. Conditional exclusion for persistent routing (doesn't get reset except by this router)
            # 条件排除用于持久路由（不会被重置，除非由本路由器操作）
            self.graph.exclude_branch_conditionally(self._id, output_name=route_to_stop)

    def true_response(self) -> Message:
        """条件为真时的响应处理，返回 true_case_message 并停止 false 分支。"""
        result = self.evaluate_condition(
            self.input_text, self.match_text, self.operator, case_sensitive=self.case_sensitive
        )

        # Check if we should force output due to max_iterations on default route
        # 检查是否因达到最大迭代次数且默认路由为 true 而强制输出
        current_iteration = self.ctx.get(f"{self._id}_iteration", 0)
        force_output = current_iteration >= self.max_iterations and self.default_route == "true_result"

        if result or force_output:
            self.status = self.true_case_message
            if not force_output:  # Only stop the other branch if not forcing due to max iterations
                # 仅在非强制输出时停止另一分支，避免打破循环时误操作
                self.iterate_and_stop_once("false_result")
            return self.true_case_message
        # 条件为假时，停止 true 分支并返回空消息
        self.iterate_and_stop_once("true_result")
        return Message(content="")

    def false_response(self) -> Message:
        """条件为假时的响应处理，返回 false_case_message 并停止 true 分支。"""
        result = self.evaluate_condition(
            self.input_text, self.match_text, self.operator, case_sensitive=self.case_sensitive
        )

        if not result:
            self.status = self.false_case_message
            self.iterate_and_stop_once("true_result")
            return self.false_case_message

        # 条件为真时，停止 false 分支并返回空消息
        self.iterate_and_stop_once("false_result")
        return Message(content="")

    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None) -> dict:
        """动态更新构建配置：当运算符为正则时隐藏大小写敏感选项，否则恢复该选项。"""
        if field_name == "operator":
            # 正则模式下不需要大小写敏感选项，从构建配置中移除
            if field_value == "regex":
                build_config.pop("case_sensitive", None)
            # 非正则模式下，如果缺少大小写敏感选项则恢复它
            elif "case_sensitive" not in build_config:
                case_sensitive_input = next(
                    (input_field for input_field in self.inputs if input_field.name == "case_sensitive"), None
                )
                if case_sensitive_input:
                    build_config["case_sensitive"] = case_sensitive_input.to_dict()
        return build_config
