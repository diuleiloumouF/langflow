from typing import Any

from lfx.base.models.unified_models import (
    get_llm,
    handle_model_input_update,
)
from lfx.custom import Component
from lfx.io import (
    BoolInput,
    MessageInput,
    MessageTextInput,
    ModelInput,
    MultilineInput,
    Output,
    SecretStrInput,
    TableInput,
)
from lfx.schema.message import Message
from lfx.schema.table import EditMode
from lfx.schema.token_usage import extract_usage_from_message


# 智能路由器组件 - 基于 LLM 分类将输入消息路由到不同的输出通道
class SmartRouterComponent(Component):
    # 组件显示名称
    display_name = "Smart Router"
    # 组件描述：使用基于 LLM 的分类来路由输入消息
    description = "Routes an input message using LLM-based categorization."
    # 组件图标
    icon = "route"
    # 组件内部名称
    name = "SmartRouter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 当前匹配的分类索引（用于多个输出之间的状态协调）
        self._matched_category = None
        # 缓存的 LLM 分类结果，避免重复调用 LLM
        self._categorization_result: str | None = None

    # 组件输入定义
    inputs = [
        # LLM 模型选择输入
        ModelInput(
            name="model",
            display_name="Language Model",
            info="Select your model provider",
            real_time_refresh=True,
            required=True,
        ),
        # API 密钥输入（可选，覆盖全局设置）
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            info="Overrides global provider settings. Leave blank to use your pre-configured API Key.",
            real_time_refresh=True,
            advanced=True,
        ),
        # 主文本输入 - 需要被分类和路由的内容
        MessageTextInput(
            name="input_text",
            display_name="Input",
            info="The primary text input for the operation.",
            required=True,
        ),
        # 路由规则表 - 定义分类类别和可选的自定义输出值
        TableInput(
            name="routes",
            display_name="Routes",
            info=(
                "Define the categories for routing. Each row should have a route/category name "
                "and optionally a custom output value."
            ),
            # 路由表的列定义
            table_schema=[
                {
                    # 路由名称（同时用作输出名称和分类匹配）
                    "name": "route_category",
                    "display_name": "Route Name",
                    "type": "str",
                    "description": "Name for the route (used for both output name and category matching)",
                    "edit_mode": EditMode.INLINE,
                },
                {
                    # 路由描述（帮助 LLM 理解分类含义）
                    "name": "route_description",
                    "display_name": "Route Description",
                    "type": "str",
                    "description": "Description of when this route should be used (helps LLM understand the category)",
                    "default": "",
                    "edit_mode": EditMode.POPOVER,
                },
                {
                    # 路由匹配时的自定义输出消息（可选）
                    "name": "output_value",
                    "display_name": "Route Message (Optional)",
                    "type": "str",
                    "description": (
                        "Optional message to send when this route is matched."
                        "Leave empty to pass through the original input text."
                    ),
                    "default": "",
                    "edit_mode": EditMode.POPOVER,
                },
            ],
            # 默认路由规则：正面和负面反馈分类
            value=[
                {
                    "route_category": "Positive",
                    "route_description": "Positive feedback, satisfaction, or compliments",
                    "output_value": "",
                },
                {
                    "route_category": "Negative",
                    "route_description": "Complaints, issues, or dissatisfaction",
                    "output_value": "",
                },
            ],
            real_time_refresh=True,
            required=True,
        ),
        # 覆盖输出消息 - 优先级最高，填写后替换所有路由的输出
        MessageInput(
            name="message",
            display_name="Override Output",
            info=(
                "Optional override message that will replace both the Input and Output Value "
                "for all routes when filled."
            ),
            required=False,
            advanced=True,
        ),
        # 是否启用 Else 输出 - 当没有分类匹配时使用
        BoolInput(
            name="enable_else_output",
            display_name="Include Else Output",
            info="Include an Else output for cases that don't match any route.",
            value=False,
            advanced=True,
            real_time_refresh=True,
        ),
        # 自定义提示词 - 附加到基础分类提示词之后
        MultilineInput(
            name="custom_prompt",
            display_name="Additional Instructions",
            info=(
                "Additional instructions for LLM-based categorization. "
                "These will be added to the base prompt. "
                "Use {input_text} for the input text and {routes} for the available categories."
            ),
            advanced=True,
        ),
    ]

    # 组件输出定义（动态生成，初始为空）
    outputs: list[Output] = []

    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        # 根据用户选择动态更新构建配置（如模型选项过滤）
        """Dynamically update build config with user-filtered model options."""
        return handle_model_input_update(self, build_config, field_value, field_name)

    def update_outputs(self, frontend_node: dict, field_name: str, field_value: Any) -> dict:
        # 根据路由表中的类别动态创建输出端口
        """Create a dynamic output for each category in the categories table."""
        if field_name in {"routes", "enable_else_output", "model"}:
            # 重置输出列表
            frontend_node["outputs"] = []

            # 获取路由数据：如果当前变更的是 routes 字段则使用新值，否则从组件状态获取
            # Get the routes data - either from field_value (if routes field) or from component state
            routes_data = field_value if field_name == "routes" else getattr(self, "routes", [])

            # 为每个路由类别添加动态输出端口，所有输出共用同一个处理方法
            # Add a dynamic output for each category - all using the same method
            for i, row in enumerate(routes_data):
                route_category = row.get("route_category", f"Category {i + 1}")
                frontend_node["outputs"].append(
                    Output(
                        display_name=route_category,
                        name=f"category_{i + 1}_result",
                        method="process_case",
                        group_outputs=True,
                    )
                )
            # 仅在启用 Else 输出时添加默认输出端口
            # Add default output only if enabled
            if field_name == "enable_else_output":
                enable_else = field_value
            else:
                enable_else = getattr(self, "enable_else_output", False)

            if enable_else:
                frontend_node["outputs"].append(
                    Output(display_name="Else", name="default_result", method="default_response", group_outputs=True)
                )
        return frontend_node

    def _get_categorization(self) -> str:
        # 执行 LLM 分类并缓存结果，确保每次组件执行只调用一次 LLM
        """Perform LLM categorization and cache the result.

        This ensures the LLM is called only once per component execution,
        regardless of how many outputs are connected.
        """
        # 如果已有缓存结果则直接返回
        # Return cached result if available
        if self._categorization_result is not None:
            return self._categorization_result

        # 获取路由配置、输入文本和 LLM 实例
        categories = getattr(self, "routes", [])
        input_text = getattr(self, "input_text", "")
        llm = get_llm(model=self.model, user_id=self.user_id, api_key=self.api_key)

        # 没有 LLM 或分类配置时返回 NONE
        if not llm or not categories:
            self.status = "No LLM provided for categorization"
            self._categorization_result = "NONE"
            return self._categorization_result

        # 构建分类信息列表，包含每个类别的名称和描述
        # Create prompt for categorization
        category_info = []
        for i, category in enumerate(categories):
            cat_name = category.get("route_category", f"Category {i + 1}")
            cat_desc = category.get("route_description", "")
            if cat_desc and cat_desc.strip():
                category_info.append(f'"{cat_name}": {cat_desc}')
            else:
                category_info.append(f'"{cat_name}"')

        # 将类别信息格式化为带列表符号的文本
        categories_text = "\n".join([f"- {info}" for info in category_info if info])

        # 构建基础分类提示词
        # Create base prompt
        base_prompt = (
            f"You are a text classifier. Given the following text and categories, "
            f"determine which category best matches the text.\n\n"
            f'Text to classify: "{input_text}"\n\n'
            f"Available categories:\n{categories_text}\n\n"
            f"Respond with ONLY the exact category name that best matches the text. "
            f'If none match well, respond with "NONE".\n\n'
            f"Category:"
        )

        # 如果提供了自定义提示词，将其作为附加指令追加到基础提示词
        # Use custom prompt as additional instructions if provided
        custom_prompt = getattr(self, "custom_prompt", "")
        if custom_prompt and custom_prompt.strip():
            self.status = "Using custom prompt as additional instructions"
            # 构建简化的路由名称列表，用于模板变量替换
            simple_routes = ", ".join(
                [f'"{cat.get("route_category", f"Category {i + 1}")}"' for i, cat in enumerate(categories)]
            )
            # 将 {input_text} 和 {routes} 模板变量替换为实际值
            formatted_custom = custom_prompt.format(input_text=input_text, routes=simple_routes)
            prompt = f"{base_prompt}\n\nAdditional Instructions:\n{formatted_custom}"
        else:
            self.status = "Using default prompt for LLM categorization"
            prompt = base_prompt

        self.status = f"Prompt sent to LLM:\n{prompt}"

        try:
            # 调用 LLM 进行分类，支持两种调用方式：invoke 方法或直接调用
            if hasattr(llm, "invoke"):
                response = llm.invoke(prompt)
                # 提取 token 使用量信息
                self._token_usage = extract_usage_from_message(response)
                if hasattr(response, "content"):
                    # LangChain 风格的响应对象
                    categorization = response.content.strip().strip('"')
                else:
                    categorization = str(response).strip().strip('"')
            else:
                # 直接调用方式（兼容不支持 invoke 的模型）
                categorization = str(llm(prompt)).strip().strip('"')

            self.status = f"LLM response: '{categorization}'"
            self._categorization_result = categorization
        except RuntimeError as e:
            # LLM 调用失败时默认返回 NONE
            self.status = f"Error in LLM categorization: {e!s}"
            self._categorization_result = "NONE"

        return self._categorization_result

    def process_case(self) -> Message:
        # 处理所有分类：使用 LLM 分类后返回匹配类别对应的消息
        """Process all categories using LLM categorization and return message for matching category."""
        # 首次调用时清除之前的匹配状态
        # Clear any previous match state (only on first call)
        if self._categorization_result is None:
            self._matched_category = None

        # 获取路由配置和输入文本
        # Get categories and input text
        categories = getattr(self, "routes", [])
        input_text = getattr(self, "input_text", "")

        # 获取缓存的分类结果（仅在首次调用时执行 LLM）
        # Get the cached categorization result (performs LLM call only once)
        categorization = self._get_categorization()

        # 根据 LLM 响应查找匹配的分类（不区分大小写）
        # Find matching category based on LLM response
        matched_category = None
        for i, category in enumerate(categories):
            route_category = category.get("route_category", "")
            if categorization.lower() == route_category.lower():
                matched_category = i
                self.status = f"MATCH FOUND! Category {i + 1} matched with '{categorization}'"
                break

        if matched_category is not None:
            # 记录匹配的分类索引，供其他输出方法检查
            # Store the matched category for other outputs to check
            self._matched_category = matched_category

            # 停止所有未匹配的分类输出端口
            # Stop all category outputs except the matched one
            for i in range(len(categories)):
                if i != matched_category:
                    self.stop(f"category_{i + 1}_result")

            # 如果启用了 Else 输出，也停止它
            # Also stop the default output (if it exists)
            enable_else = getattr(self, "enable_else_output", False)
            if enable_else:
                self.stop("default_result")

            route_category = categories[matched_category].get("route_category", f"Category {matched_category + 1}")
            self.status = f"Categorized as {route_category}"

            # 优先级检查：覆盖输出 > 自定义输出 > 原始输入
            # Check if there's an override output (takes precedence over everything)
            override_output = getattr(self, "message", None)
            if (
                override_output
                and hasattr(override_output, "text")
                and override_output.text
                and str(override_output.text).strip()
            ):
                return Message(text=str(override_output.text))
            if override_output and isinstance(override_output, str) and override_output.strip():
                return Message(text=str(override_output))

            # 检查该分类是否有自定义输出值
            # Check if there's a custom output value for this category
            custom_output = categories[matched_category].get("output_value", "")
            # Treat None, empty string, or whitespace as blank
            if custom_output and str(custom_output).strip() and str(custom_output).strip().lower() != "none":
                # Use custom output value
                return Message(text=str(custom_output))
            # 默认使用原始输入作为输出
            # Use input as default output
            return Message(text=input_text)
        # 没有匹配的分类，停止所有分类输出
        # No match found, stop all category outputs
        for i in range(len(categories)):
            self.stop(f"category_{i + 1}_result")

        # 检查是否启用了 Else 输出
        # Check if else output is enabled
        enable_else = getattr(self, "enable_else_output", False)
        if enable_else:
            # 停止 process_case 自身的输出，由 default_response 处理 Else 场景
            # The default_response will handle the else case
            self.stop("process_case")
            return Message(text="")
        # 未启用 Else 输出，且无匹配结果，不产生任何输出
        # No else output, so no output at all
        self.status = "No match found and Else output is disabled"
        return Message(text="")

    def default_response(self) -> Message:
        # 处理 Else 场景：当没有任何条件匹配时的默认响应
        """Handle the else case when no conditions match."""
        enable_else = getattr(self, "enable_else_output", False)
        if not enable_else:
            self.status = "Else output is disabled"
            return Message(text="")

        categories = getattr(self, "routes", [])
        input_text = getattr(self, "input_text", "")

        # 获取缓存的分类结果（仅在未执行过 LLM 调用时执行）
        # Get the cached categorization result (performs LLM call only if not already done)
        categorization = self._get_categorization()

        # 检查分类结果是否匹配了某个路由类别
        # Check if the categorization matches any category
        has_match = False
        for i, category in enumerate(categories):
            route_category = category.get("route_category", "")
            if categorization.lower() == route_category.lower():
                has_match = True
                self.status = f"Match found for '{categorization}' (Category {i + 1}), stopping default_response"
                break

        if has_match:
            # 如果有分类匹配了，停止默认输出（由 process_case 处理匹配的输出）
            # A case matches, stop this output
            self.stop("default_result")
            return Message(text="")

        # 没有任何匹配：优先使用覆盖输出，其次使用原始输入
        # No case matches, check for override output first, then use input as default
        override_output = getattr(self, "message", None)
        if (
            override_output
            and hasattr(override_output, "text")
            and override_output.text
            and str(override_output.text).strip()
        ):
            self.status = "Routed to Else (no match) - using override output"
            return Message(text=str(override_output.text))
        if override_output and isinstance(override_output, str) and override_output.strip():
            self.status = "Routed to Else (no match) - using override output"
            return Message(text=str(override_output))

        # 默认返回原始输入文本
        self.status = "Routed to Else (no match) - using input as default"
        return Message(text=input_text)
