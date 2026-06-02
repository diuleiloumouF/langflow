"""ALTK Agent Component that combines pre-tool validation and post-tool processing capabilities."""

# ALTK Agent 组件：组合了工具执行前验证和工具执行后处理能力

from lfx.base.agents.altk_base_agent import ALTKBaseAgentComponent
from lfx.base.agents.altk_tool_wrappers import (
    PostToolProcessingWrapper,
    PreToolValidationWrapper,
)
from lfx.base.models.model_input_constants import MODEL_PROVIDERS_DICT, MODELS_METADATA
from lfx.components.models_and_agents.memory import MemoryComponent
from lfx.inputs.inputs import BoolInput
from lfx.io import DropdownInput, IntInput, Output
from lfx.log.logger import logger


def set_advanced_true(component_input):
    """Set the advanced flag to True for a component input."""
    # 将组件输入的 advanced 标志设置为 True（用于在 UI 中默认隐藏该输入）
    component_input.advanced = True
    return component_input


# 支持的模型提供商列表
MODEL_PROVIDERS_LIST = ["Anthropic", "OpenAI"]
# 需要被覆盖的输入字段名称
INPUT_NAMES_TO_BE_OVERRIDDEN = ["agent_llm"]


def get_parent_agent_inputs():
    """获取父类 ALTKBaseAgentComponent 的输入，排除需要被覆盖的字段"""
    return [
        input_field
        for input_field in ALTKBaseAgentComponent.inputs
        if input_field.name not in INPUT_NAMES_TO_BE_OVERRIDDEN
    ]


# === Combined ALTK Agent Component ===
# === 组合式 ALTK Agent 组件 ===


class ALTKAgentComponent(ALTKBaseAgentComponent):
    """ALTK Agent with both pre-tool validation and post-tool processing capabilities.

    This agent combines the functionality of both ALTKAgent and AgentReflection components,
    implementing a modular pipeline for tool processing that can be extended with
    additional capabilities in the future.
    """

    # ALTK Agent：同时具备工具执行前验证和工具执行后处理能力。
    # 该代理组合了 ALTKAgent 和 AgentReflection 组件的功能，
    # 实现了模块化的工具处理管道，未来可通过扩展添加更多能力。

    # 组件显示名称
    display_name: str = "ALTK Agent"
    # 组件描述
    description: str = "Advanced agent with both pre-tool validation and post-tool processing capabilities."
    # 组件文档链接
    documentation: str = "https://docs.langflow.org/bundles-altk"
    # 组件图标
    icon = "zap"
    # 标记为 beta 版本
    beta = True
    # 组件内部名称
    name = "ALTK Agent"

    # 从 MemoryComponent 获取记忆相关输入，并将所有输入设为高级选项
    memory_inputs = [set_advanced_true(component_input) for component_input in MemoryComponent().inputs]

    # 从 OpenAI 输入中过滤掉 json_mode，因为结构化输出的处理方式不同
    # Filter out json_mode from OpenAI inputs since we handle structured output differently
    if "OpenAI" in MODEL_PROVIDERS_DICT:
        openai_inputs_filtered = [
            input_field
            for input_field in MODEL_PROVIDERS_DICT["OpenAI"]["inputs"]
            if not (hasattr(input_field, "name") and input_field.name == "json_mode")
        ]
    else:
        openai_inputs_filtered = []

    # 组件输入定义
    inputs = [
        # 模型提供商下拉选择框
        DropdownInput(
            name="agent_llm",
            display_name="Model Provider",
            info="The provider of the language model that the agent will use to generate responses.",
            options=[*MODEL_PROVIDERS_LIST],
            value="OpenAI",
            real_time_refresh=True,
            refresh_button=False,
            input_types=[],
            options_metadata=[MODELS_METADATA[key] for key in MODEL_PROVIDERS_LIST if key in MODELS_METADATA],
        ),
        # 继承父类的输入字段
        *get_parent_agent_inputs(),
        # 启用工具验证开关（使用 SPARC 在执行前验证工具调用）
        BoolInput(
            name="enable_tool_validation",
            display_name="Tool Validation",
            info="Validates tool calls using SPARC before execution.",
            value=True,
        ),
        # 启用工具执行后 JSON 处理开关
        BoolInput(
            name="enable_post_tool_reflection",
            display_name="Post Tool JSON Processing",
            info="Processes tool output through JSON analysis.",
            value=True,
        ),
        # 响应处理大小阈值：只有当工具输出超过此字符数时才进行后处理
        IntInput(
            name="response_processing_size_threshold",
            display_name="Response Processing Size Threshold",
            value=100,
            info="Tool output is post-processed only if response exceeds this character threshold.",
            advanced=True,
        ),
    ]
    # 组件输出定义
    outputs = [
        Output(name="response", display_name="Response", method="message_response"),
    ]

    def configure_tool_pipeline(self) -> None:
        """Configure the tool pipeline with wrappers based on enabled features."""
        # 根据启用的功能配置工具管道的包装器
        wrappers = []

        # 首先添加工具执行后处理包装器（作为最内层包装器）
        # Add post-tool processing first (innermost wrapper)
        if self.enable_post_tool_reflection:
            logger.info("Enabling Post-Tool Processing Wrapper!")
            post_processor = PostToolProcessingWrapper(
                response_processing_size_threshold=self.response_processing_size_threshold
            )
            wrappers.append(post_processor)

        # 最后添加工具执行前验证包装器（作为最外层包装器）
        # Add pre-tool validation last (outermost wrapper)
        if self.enable_tool_validation:
            logger.info("Enabling Pre-Tool Validation Wrapper!")
            pre_validator = PreToolValidationWrapper()
            wrappers.append(pre_validator)

        # 将包装器列表配置到管道管理器中
        self.pipeline_manager.configure_wrappers(wrappers)

    def update_runnable_instance(self, agent, runnable, tools):
        """Override to add tool specs update for validation wrappers."""
        # 重写父类方法，为验证包装器添加工具规格更新

        # 获取上下文信息（从父类复制）
        # Get context info (copied from parent)
        user_query = self.get_user_query()
        conversation_context = self.build_conversation_context()

        # 初始化管道（确保 configure_tool_pipeline 被调用）
        # Initialize pipeline (this ensures configure_tool_pipeline is called)
        self._initialize_tool_pipeline()

        # 在处理之前更新验证包装器的工具规格
        # Update tool specs for validation wrappers BEFORE processing
        for wrapper in self.pipeline_manager.wrappers:
            if isinstance(wrapper, PreToolValidationWrapper) and tools:
                wrapper.tool_specs = wrapper.convert_langchain_tools_to_sparc_tool_specs_format(tools)

        # 使用更新后的规格处理工具
        # Process tools with updated specs
        processed_tools = self.pipeline_manager.process_tools(
            list(tools or []),
            agent=agent,
            user_query=user_query,
            conversation_context=conversation_context,
        )

        # 将处理后的工具设置到 runnable 上
        runnable.tools = processed_tools
        return runnable

    def __init__(self, **kwargs):
        """Initialize ALTK agent with input normalization for Data.to_lc_message() inconsistencies."""
        # 初始化 ALTK 代理，并对 Data.to_lc_message() 的不一致性进行输入标准化
        super().__init__(**kwargs)

        # 如果 input_value 使用了 Data.to_lc_message()，则用代理包装以提供一致的内容格式
        # If input_value uses Data.to_lc_message(), wrap it to provide consistent content
        if hasattr(self.input_value, "to_lc_message") and callable(self.input_value.to_lc_message):
            self.input_value = self._create_normalized_input_proxy(self.input_value)

    def _create_normalized_input_proxy(self, original_input):
        """Create a proxy that normalizes to_lc_message() content format."""
        # 创建一个代理对象，用于标准化 to_lc_message() 的内容格式

        class NormalizedInputProxy:
            """标准化输入代理类：将 to_lc_message() 返回的消息内容统一为字符串格式"""

            def __init__(self, original):
                # 保存原始输入对象的引用
                self._original = original

            def __getattr__(self, name):
                # 如果访问的是 to_lc_message 属性，返回标准化版本
                if name == "to_lc_message":
                    return self._normalized_to_lc_message
                # 否则委托给原始对象
                return getattr(self._original, name)

            def _normalized_to_lc_message(self):
                """Return a message with normalized string content."""
                # 返回内容经过标准化的消息
                original_msg = self._original.to_lc_message()

                # 如果内容是列表格式，将其标准化为字符串
                # If content is in list format, normalize it to string
                if hasattr(original_msg, "content") and isinstance(original_msg.content, list):
                    from langchain_core.messages import AIMessage, HumanMessage

                    from lfx.base.agents.altk_base_agent import (
                        normalize_message_content,
                    )

                    # 使用 normalize_message_content 将列表内容转为字符串
                    normalized_content = normalize_message_content(original_msg)

                    # 根据原始消息类型创建新的字符串内容消息
                    # Create new message with string content
                    if isinstance(original_msg, HumanMessage):
                        return HumanMessage(content=normalized_content)
                    return AIMessage(content=normalized_content)

                # 如果已经是字符串格式，直接返回原始消息
                # Return original if already string format
                return original_msg

            def __str__(self):
                return str(self._original)

            def __repr__(self):
                return f"NormalizedInputProxy({self._original!r})"

        return NormalizedInputProxy(original_input)
