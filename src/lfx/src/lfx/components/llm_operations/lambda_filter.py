from __future__ import annotations

import json
import re
from collections.abc import Callable  # noqa: TC003 - required at runtime for dynamic exec()
from typing import Any

from lfx.base.models.unified_models import (
    get_llm,
    handle_model_input_update,
)
from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, IntInput, ModelInput, MultilineInput, Output, SecretStrInput
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.schema.message import Message
from lfx.schema.token_usage import extract_usage_from_message
from lfx.utils.constants import MESSAGE_SENDER_AI

# 文本转换提示词：用于指导 LLM 根据自然语言指令生成 lambda 函数，对文本进行转换
TEXT_TRANSFORM_PROMPT = (
    "Given this text, create a Python lambda function that transforms it "
    "according to the instruction.\n"
    "The lambda should take a string parameter and return the transformed string.\n\n"
    "Text Preview:\n{text_preview}\n\n"
    "Instruction: {instruction}\n\n"
    "Return ONLY the lambda function and nothing else. No need for ```python or whatever.\n"
    "Just a string starting with lambda.\n"
    "Example: lambda text: text.upper()"
)

# 数据转换提示词：用于指导 LLM 根据数据结构和示例生成 lambda 函数，对结构化数据进行过滤或转换
DATA_TRANSFORM_PROMPT = (
    "Given this data structure and examples, create a Python lambda function "
    "that implements the following instruction:\n\n"
    "Data Structure:\n{dump_structure}\n\n"
    "Example Items:\n{data_sample}\n\n"
    "Instruction: {instruction}\n\n"
    "Return ONLY the lambda function and nothing else. No need for ```python or whatever.\n"
    "Just a string starting with lambda."
)


class LambdaFilterComponent(Component):
    """智能转换组件：使用 LLM 根据自然语言指令生成 lambda 函数，对结构化数据和消息进行过滤或转换。"""

    display_name = "Smart Transform"
    # 组件描述：使用 LLM 生成函数来过滤或转换结构化数据和消息
    description = "Uses an LLM to generate a function for filtering or transforming structured data and messages."
    documentation: str = "https://docs.langflow.org/smart-transform"
    icon = "square-function"
    name = "Smart Transform"

    # 输入参数定义
    inputs = [
        DataInput(
            name="data",
            display_name="JSON",
            # 要使用 lambda 函数进行过滤或转换的结构化数据或文本消息
            info="The structured data or text messages to filter or transform using a lambda function.",
            input_types=["Data", "JSON", "DataFrame", "Table", "Message"],
            is_list=True,
            required=True,
        ),
        ModelInput(
            name="model",
            display_name="Language Model",
            # 选择模型提供商
            info="Select your model provider",
            real_time_refresh=True,
            required=True,
        ),
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            # 覆盖全局提供商设置，留空则使用预配置的 API Key
            info="Overrides global provider settings. Leave blank to use your pre-configured API Key.",
            real_time_refresh=True,
            advanced=True,
        ),
        MultilineInput(
            name="filter_instruction",
            display_name="Instructions",
            # 自然语言指令，描述如何使用 lambda 函数过滤或转换数据
            info=(
                "Natural language instructions for how to filter or transform the data using a lambda function. "
                "Examples: 'Filter the data to only include items where status is active', "
                "'Convert the text to uppercase', 'Keep only first 100 characters'"
            ),
            value="Transform the data to...",
            required=True,
        ),
        IntInput(
            name="sample_size",
            display_name="Sample Size",
            # 对于大数据集，从头部/尾部采样的项目数量
            info="For large datasets, number of items to sample from head/tail.",
            value=1000,
            advanced=True,
        ),
        IntInput(
            name="max_size",
            display_name="Max Size",
            # 数据被视为"大"时的字符数阈值
            info="Number of characters for the data to be considered large.",
            value=30000,
            advanced=True,
        ),
    ]

    # 输出定义：支持 Data、DataFrame、Message 三种输出格式
    outputs = [
        Output(
            display_name="Output",
            name="data_output",
            method="process_as_data",
        ),
        Output(
            display_name="Output",
            name="dataframe_output",
            method="process_as_dataframe",
        ),
        Output(
            display_name="Output",
            name="message_output",
            method="process_as_message",
        ),
    ]

    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        """Dynamically update build config with user-filtered model options."""
        # 动态更新构建配置，根据用户筛选的模型选项刷新界面
        return handle_model_input_update(self, build_config, field_value, field_name)

    def get_data_structure(self, data):
        """Extract the structure of data, replacing values with their types."""
        # 递归提取数据结构，将值替换为其类型名称，用于向 LLM 展示数据骨架
        if isinstance(data, list):
            # For lists, get structure of first item if available
            if data:
                return [self.get_data_structure(data[0])]
            return []
        if isinstance(data, dict):
            return {k: self.get_data_structure(v) for k, v in data.items()}
        # For primitive types, return the type name
        # 对于基本类型，返回类型名称（如 int、str 等）
        return type(data).__name__

    def _validate_lambda(self, lambda_text: str) -> bool:
        """Validate the provided lambda function text."""
        # Return False if the lambda function does not start with 'lambda' or does not contain a colon
        # 验证 lambda 文本是否以 "lambda" 开头且包含冒号
        return lambda_text.strip().startswith("lambda") and ":" in lambda_text

    def _get_input_type_name(self) -> str:
        """Detect and return the input type name for error messages."""
        # 检测输入数据的类型名称，用于生成错误信息
        if isinstance(self.data, Message):
            return "Message"
        if isinstance(self.data, DataFrame):
            return "DataFrame"
        if isinstance(self.data, Data):
            return "Data"
        if isinstance(self.data, list) and len(self.data) > 0:
            first = self.data[0]
            if isinstance(first, Message):
                return "Message"
            if isinstance(first, DataFrame):
                return "DataFrame"
            if isinstance(first, Data):
                return "Data"
        return "unknown"

    def _extract_message_text(self) -> str:
        """Extract text content from Message input(s)."""
        # 从 Message 类型输入中提取文本内容
        if isinstance(self.data, Message):
            return self.data.text or ""

        # 多条消息用双换行符拼接
        texts = [msg.text or "" for msg in self.data if isinstance(msg, Message)]
        return "\n\n".join(texts) if len(texts) > 1 else (texts[0] if texts else "")

    def _extract_structured_data(self) -> dict | list:
        """Extract structured data from Data or DataFrame input(s)."""
        # 从 Data 或 DataFrame 输入中提取结构化数据
        if isinstance(self.data, DataFrame):
            # DataFrame 转换为记录列表格式
            return self.data.to_dict(orient="records")

        if hasattr(self.data, "data"):
            return self.data.data

        if not isinstance(self.data, list):
            return self.data

        # 合并多个输入项中的数据
        combined_data: list[dict] = []
        for item in self.data:
            if isinstance(item, DataFrame):
                combined_data.extend(item.to_dict(orient="records"))
            elif hasattr(item, "data"):
                if isinstance(item.data, dict):
                    combined_data.append(item.data)
                elif isinstance(item.data, list):
                    combined_data.extend(item.data)

        # 如果合并后只有一条记录，直接返回该记录而非列表
        if len(combined_data) == 1 and isinstance(combined_data[0], dict):
            return combined_data[0]
        if len(combined_data) == 0:
            return {}
        return combined_data

    def _is_message_input(self) -> bool:
        """Check if input is Message type."""
        # 判断输入是否为 Message 类型（单条或列表形式）
        if isinstance(self.data, Message):
            return True
        return isinstance(self.data, list) and len(self.data) > 0 and isinstance(self.data[0], Message)

    def _build_text_prompt(self, text: str) -> str:
        """Build prompt for text/Message transformation."""
        # 为文本/消息转换构建提示词，对超长文本进行截取采样
        text_length = len(text)
        if text_length > self.max_size:
            # 文本过长时，只保留首尾各 sample_size 个字符作为预览
            text_preview = (
                f"Text length: {text_length} characters\n\n"
                f"First {self.sample_size} characters:\n{text[: self.sample_size]}\n\n"
                f"Last {self.sample_size} characters:\n{text[-self.sample_size :]}"
            )
        else:
            text_preview = text

        return TEXT_TRANSFORM_PROMPT.format(text_preview=text_preview, instruction=self.filter_instruction)

    def _build_data_prompt(self, data: dict | list) -> str:
        """Build prompt for structured data transformation."""
        # 为结构化数据转换构建提示词，包含数据骨架和采样数据
        dump = json.dumps(data)
        dump_structure = json.dumps(self.get_data_structure(data))

        if len(dump) > self.max_size:
            # 数据过长时，只保留首尾各 sample_size 个字符作为预览
            data_sample = (
                f"Data is too long to display...\n\nFirst lines (head): {dump[: self.sample_size]}\n\n"
                f"Last lines (tail): {dump[-self.sample_size :]}"
            )
        else:
            data_sample = dump

        return DATA_TRANSFORM_PROMPT.format(
            dump_structure=dump_structure, data_sample=data_sample, instruction=self.filter_instruction
        )

    def _parse_lambda_from_response(self, response_text: str) -> Callable[[Any], Any]:
        """Extract and validate lambda function from LLM response."""
        # 从 LLM 响应中使用正则提取 lambda 函数表达式
        lambda_match = re.search(r"lambda\s+\w+\s*:.*?(?=\n|$)", response_text)
        if not lambda_match:
            msg = f"Could not find lambda in response: {response_text}"
            raise ValueError(msg)

        lambda_text = lambda_match.group().strip()
        self.log(f"Generated lambda: {lambda_text}")

        # 验证提取到的 lambda 格式是否合法
        if not self._validate_lambda(lambda_text):
            msg = f"Invalid lambda format: {lambda_text}"
            raise ValueError(msg)

        # 将 lambda 字符串动态执行为可调用的函数对象
        return eval(lambda_text)  # noqa: S307

    async def _execute_lambda(self) -> Any:
        """Generate and execute a lambda function based on input type."""
        # 根据输入类型（消息或结构化数据）提取数据并构建对应的提示词
        if self._is_message_input():
            data: Any = self._extract_message_text()
            prompt = self._build_text_prompt(data)
        else:
            data = self._extract_structured_data()
            prompt = self._build_data_prompt(data)

        # 调用 LLM 生成 lambda 函数
        llm = get_llm(model=self.model, user_id=self.user_id, api_key=self.api_key)
        response = await llm.ainvoke(prompt)
        # 记录 token 使用量
        self._token_usage = extract_usage_from_message(response)
        response_text = response.content if hasattr(response, "content") else str(response)

        # 解析并执行生成的 lambda 函数，将数据传入执行
        fn = self._parse_lambda_from_response(response_text)
        return fn(data)

    def _handle_process_error(self, error: Exception, output_type: str) -> None:
        """Handle errors from process methods with context-aware messages."""
        # 处理处理过程中的错误，生成包含输入类型上下文的错误信息
        input_type = self._get_input_type_name()
        error_msg = (
            f"Failed to convert result to {output_type} output. "
            f"Error: {error}. "
            f"Input type was {input_type}. "
            f"Try using the same output type as the input."
        )
        raise ValueError(error_msg) from error

    def _convert_result_to_data(self, result: Any) -> Data:
        """Convert lambda result to Data object."""
        # 将 lambda 执行结果转换为 Data 对象
        if isinstance(result, dict):
            return Data(data=result)
        if isinstance(result, list):
            return Data(data={"_results": result})
        return Data(data={"text": str(result)})

    def _convert_result_to_dataframe(self, result: Any) -> DataFrame:
        """Convert lambda result to DataFrame object."""
        # 将 lambda 执行结果转换为 DataFrame 对象
        if isinstance(result, list):
            # 列表中每个元素都是字典时直接作为记录
            if all(isinstance(item, dict) for item in result):
                return DataFrame(result)
            # 否则将每个值包装为 {"value": item} 格式
            return DataFrame([{"value": item} for item in result])
        if isinstance(result, dict):
            return DataFrame([result])
        return DataFrame([{"value": str(result)}])

    def _convert_result_to_message(self, result: Any) -> Message:
        """Convert lambda result to Message object."""
        # 将 lambda 执行结果转换为 Message 对象
        if isinstance(result, str):
            return Message(text=result, sender=MESSAGE_SENDER_AI)
        if isinstance(result, list):
            # 列表结果拼接为换行分隔的文本
            text = "\n".join(str(item) for item in result)
            return Message(text=text, sender=MESSAGE_SENDER_AI)
        if isinstance(result, dict):
            # 字典结果格式化为 JSON 字符串
            text = json.dumps(result, indent=2)
            return Message(text=text, sender=MESSAGE_SENDER_AI)
        return Message(text=str(result), sender=MESSAGE_SENDER_AI)

    async def process_as_data(self) -> Data:
        """Process the data and return as a Data object."""
        # 以 Data 格式处理数据：执行 lambda 并将结果转换为 Data 对象
        try:
            result = await self._execute_lambda()
            return self._convert_result_to_data(result)
        except Exception as e:  # noqa: BLE001 - dynamic lambda can raise any exception
            self._handle_process_error(e, "Data")

    async def process_as_dataframe(self) -> DataFrame:
        """Process the data and return as a DataFrame."""
        # 以 DataFrame 格式处理数据：执行 lambda 并将结果转换为 DataFrame 对象
        try:
            result = await self._execute_lambda()
            return self._convert_result_to_dataframe(result)
        except Exception as e:  # noqa: BLE001 - dynamic lambda can raise any exception
            self._handle_process_error(e, "DataFrame")

    async def process_as_message(self) -> Message:
        """Process the data and return as a Message."""
        # 以 Message 格式处理数据：执行 lambda 并将结果转换为 Message 对象
        try:
            result = await self._execute_lambda()
            return self._convert_result_to_message(result)
        except Exception as e:  # noqa: BLE001 - dynamic lambda can raise any exception
            self._handle_process_error(e, "Message")
