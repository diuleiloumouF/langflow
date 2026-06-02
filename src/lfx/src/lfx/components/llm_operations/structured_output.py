# 导入 Pydantic 相关工具，用于构建和创建数据模型
from pydantic import BaseModel, Field, create_model

# 导入 trustcall 库，用于通过工具调用方式提取结构化输出
from trustcall import create_extractor

from lfx.base.agents.token_callback import TokenUsageCallbackHandler
from lfx.base.models.chat_result import get_chat_result
from lfx.base.models.unified_models import (
    get_llm,
    handle_model_input_update,
)
from lfx.custom.custom_component.component import Component
from lfx.helpers.base_model import build_model_from_schema
from lfx.io import (
    MessageTextInput,
    ModelInput,
    MultilineInput,
    Output,
    SecretStrInput,
    TableInput,
)
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.schema.table import EditMode


# 结构化输出组件：利用 LLM 从非结构化文本中提取结构化 JSON 数据
# 根据用户定义的 schema（字段名、类型、描述）提取数据并输出为 Data 或 DataFrame 格式
class StructuredOutputComponent(Component):
    display_name = "Structured Output"
    description = "Uses an LLM to generate structured data. Ideal for extraction and consistency."
    documentation: str = "https://docs.langflow.org/structured-output"
    name = "StructuredOutput"
    icon = "braces"

    # 组件输入参数定义
    inputs = [
        ModelInput(
            name="model",
            display_name="Language Model",
            info="Select your model provider",
            real_time_refresh=True,
            required=True,
        ),
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            info="Overrides global provider settings. Leave blank to use your pre-configured API Key.",
            real_time_refresh=True,
            advanced=True,
        ),
        MultilineInput(
            name="input_value",
            display_name="Input Message",
            info="The input message to the language model.",
            tool_mode=True,
            required=True,
        ),
        MultilineInput(
            name="system_prompt",
            display_name="Format Instructions",
            info="The instructions to the language model for formatting the output.",
            value=(
                "You are an AI that extracts structured JSON objects from unstructured text. "
                "Use a predefined schema with expected types (str, int, float, bool, dict). "
                "Extract ALL relevant instances that match the schema - if multiple patterns exist, capture them all. "
                "Fill missing or ambiguous values with defaults: null for missing values. "
                "Remove exact duplicates but keep variations that have different field values. "
                "Always return valid JSON in the expected format, never throw errors. "
                "If multiple objects can be extracted, return them all in the structured format."
            ),
            required=True,
            advanced=True,
        ),
        MessageTextInput(
            name="schema_name",
            display_name="Schema Name",
            info="Provide a name for the output data schema.",
            advanced=True,
        ),
        # 输出 schema 定义表格，用户通过表格配置提取字段的名称、描述、类型和是否为列表
        TableInput(
            name="output_schema",
            display_name="Output Schema",
            info="Define the structure and data types for the model's output.",
            required=True,
            # TODO: remove default value
            table_schema=[
                {
                    "name": "name",
                    "display_name": "Name",
                    "type": "str",
                    "description": "Specify the name of the output field.",
                    "default": "field",
                    "edit_mode": EditMode.INLINE,
                },
                {
                    "name": "description",
                    "display_name": "Description",
                    "type": "str",
                    "description": "Describe the purpose of the output field.",
                    "default": "description of field",
                    "edit_mode": EditMode.POPOVER,
                },
                {
                    "name": "type",
                    "display_name": "Type",
                    "type": "str",
                    "edit_mode": EditMode.INLINE,
                    "description": ("Indicate the data type of the output field (e.g., str, int, float, bool, dict)."),
                    "options": ["str", "int", "float", "bool", "dict"],
                    "default": "str",
                },
                {
                    "name": "multiple",
                    "display_name": "As List",
                    "type": "boolean",
                    "description": "Set to True if this output field should be a list of the specified type.",
                    "default": "False",
                    "edit_mode": EditMode.INLINE,
                },
            ],
            value=[
                {
                    "name": "field",
                    "description": "description of field",
                    "type": "str",
                    "multiple": "False",
                }
            ],
        ),
    ]

    # 组件输出定义：支持 Data 格式和 DataFrame 格式两种输出方式
    outputs = [
        Output(
            name="structured_output",
            display_name="Structured Output",
            method="build_structured_output",
        ),
        Output(
            name="dataframe_output",
            display_name="Structured Output",
            method="build_structured_dataframe",
        ),
    ]

    # 动态更新构建配置，根据用户选择的模型刷新可用选项
    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        """Dynamically update build config with user-filtered model options."""
        return handle_model_input_update(self, build_config, field_value, field_name)

    # 构建结构化输出的核心逻辑：先尝试 trustcall 方式，失败后回退到 LangChain 方式
    def build_structured_output_base(self):
        # 获取 schema 名称，默认为 "OutputModel"
        schema_name = self.schema_name or "OutputModel"

        # 获取 LLM 模型实例
        llm = get_llm(model=self.model, user_id=self.user_id, api_key=self.api_key)

        # 检查模型是否支持结构化输出
        if not hasattr(llm, "with_structured_output"):
            msg = "Language model does not support structured output."
            raise TypeError(msg)
        if not self.output_schema:
            msg = "Output schema cannot be empty"
            raise ValueError(msg)

        # 根据用户定义的 schema 构建 Pydantic 模型
        output_model_ = build_model_from_schema(self.output_schema)
        # 创建一个包含列表字段的包装模型，用于接收多条结构化输出
        output_model = create_model(
            schema_name,
            __doc__=f"A list of {schema_name}.",
            objects=(
                list[output_model_],
                Field(
                    description=f"A list of {schema_name}.",  # type: ignore[valid-type]
                    min_length=1,  # help ensure non-empty output
                ),
            ),
        )
        # 追踪配置：将 token 用量处理器注入回调链中
        # get_chat_result() 将 "get_langchain_callbacks" 作为可调用对象读取，因此用 lambda 包装列表以匹配其接口
        token_handler = TokenUsageCallbackHandler()
        base_callbacks = self.get_langchain_callbacks()
        config_dict = {
            "display_name": self.display_name,
            "get_project_name": self.get_project_name,
            "get_langchain_callbacks": lambda: [*base_callbacks, token_handler],
        }
        # 优先使用 Trustcall 提取结构化输出，失败后回退到 LangChain 方式
        result = self._extract_output_with_trustcall(llm, output_model, config_dict)
        if result is None:
            result = self._extract_output_with_langchain(llm, output_model, config_dict)
        self._token_usage = token_handler.get_usage()

        # 以下为基于 trustcall 响应结构的简化后处理逻辑
        # 处理非字典类型的响应（trustcall 通常返回字典，此处为防御性处理）
        if not isinstance(result, dict):
            return result

        # 从响应中提取第一条结果并转换为字典
        responses = result.get("responses", [])
        if not responses:
            return result

        # 将 BaseModel 实例转换为字典（会创建 "objects" 键）
        first_response = responses[0]
        structured_data = first_response
        if isinstance(first_response, BaseModel):
            structured_data = first_response.model_dump()
        # 提取 objects 数组（由于我们的 Pydantic 模型结构，该字段一定存在）
        return structured_data.get("objects", structured_data)

    # 以 Data 格式返回结构化输出：单条结果直接返回，多条结果包装在 results 中
    def build_structured_output(self) -> Data:
        output = self.build_structured_output_base()
        if not isinstance(output, list) or not output:
            # 处理空输出或非预期类型的情况
            msg = "No structured output returned"
            raise ValueError(msg)
        if len(output) == 1:
            return Data(data=output[0])
        if len(output) > 1:
            # 多条输出时，将它们包装在 results 容器中
            return Data(data={"results": output})
        return Data()

    # 以 DataFrame 格式返回结构化输出：适合表格形式展示多条提取结果
    def build_structured_dataframe(self) -> DataFrame:
        output = self.build_structured_output_base()
        if not isinstance(output, list) or not output:
            # 处理空输出或非预期类型的情况
            msg = "No structured output returned"
            raise ValueError(msg)
        if len(output) == 1:
            # 单条结果包装在列表中，以创建包含一行的 DataFrame
            return DataFrame([output[0]])
        if len(output) > 1:
            # 多条输出直接转换为 DataFrame
            return DataFrame(output)
        return DataFrame()

    # 使用 Trustcall 通过工具调用方式提取结构化输出
    # 如果模型不支持工具调用或提取失败，返回 None 以便回退到 LangChain 方式
    def _extract_output_with_trustcall(self, llm, schema: BaseModel, config_dict: dict) -> list[BaseModel] | None:
        try:
            # 创建带有结构化输出能力的 LLM 提取器，指定工具和工具选择
            llm_with_structured_output = create_extractor(llm, tools=[schema], tool_choice=schema.__name__)
            result = get_chat_result(
                runnable=llm_with_structured_output,
                system_message=self.system_prompt,
                input_value=self.input_value,
                config=config_dict,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Trustcall extraction failed, falling back to Langchain: {e} "
                "(Note: This may not be an error—some models or configurations do not support tool calling. "
                "Falling back is normal in such cases.)"
            )
            return None
        return result or None  # 发生错误或结果为空时，返回 None 以触发 LangChain 回退

    # 使用 LangChain 的 with_structured_output 方法提取结构化输出
    # 作为 Trustcall 失败后的回退方案
    def _extract_output_with_langchain(self, llm, schema: BaseModel, config_dict: dict) -> list[BaseModel] | None:
        try:
            # 使用 LangChain 的 with_structured_output 方法将 LLM 绑定到指定 schema
            llm_with_structured_output = llm.with_structured_output(schema)
            result = get_chat_result(
                runnable=llm_with_structured_output,
                system_message=self.system_prompt,
                input_value=self.input_value,
                config=config_dict,
            )
            # 如果结果是 BaseModel 实例，先转换为字典再提取 objects 字段
            if isinstance(result, BaseModel):
                result = result.model_dump()
                result = result.get("objects", result)
        except Exception as fallback_error:
            # Trustcall 和 LangChain 回退均失败时，抛出包含两个错误信息的异常
            msg = (
                f"Model does not support tool calling (trustcall failed) "
                f"and fallback with_structured_output also failed: {fallback_error}"
            )
            raise ValueError(msg) from fallback_error

        return result or None
