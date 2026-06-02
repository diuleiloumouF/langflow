# 异步编程支持
import asyncio

# JSON 序列化和反序列化
import json

# 抑制特定异常（用于静默处理 JSON 解析错误）
from contextlib import suppress
from typing import Any

# URL 拼接工具，用于构建 Ollama API 请求地址
from urllib.parse import urljoin

import httpx

# LangChain 的 Ollama 聊天模型集成
from langchain_ollama import ChatOllama

# 模型组件基类
from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec

# 根据 JSON Schema 动态构建 Pydantic 模型
from lfx.helpers.base_model import build_model_from_schema
from lfx.io import (
    BoolInput,
    DictInput,
    DropdownInput,
    FloatInput,
    IntInput,
    MessageTextInput,
    Output,
    SecretStrInput,
    SliderInput,
    StrInput,
    TableInput,
)
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.schema.table import EditMode

# localhost URL 转换工具，用于处理不同平台的 localhost 地址差异
from lfx.utils.util import transform_localhost_url

# HTTP 状态码：请求成功
HTTP_STATUS_OK = 200
# 表格输入的默认占位行，用于格式化输出字段定义
TABLE_ROW_PLACEHOLDER = {"name": "field", "description": "description of field", "type": "str", "multiple": "False"}


# Ollama 本地大语言模型组件，封装了与 Ollama API 的交互逻辑
# 支持文本生成、工具调用、结构化输出（JSON Schema）等能力
# 可输出文本、语言模型实例、JSON 数据和 DataFrame 表格
class ChatOllamaComponent(LCModelComponent):
    # 组件在画布上的显示名称
    display_name = "Ollama"
    # 组件描述，说明其用途是使用本地 Ollama LLM 生成文本
    description = "Generate text using Ollama Local LLMs."
    # 组件图标标识
    icon = "Ollama"
    # 组件内部唯一名称，用于流程 JSON 中的引用
    name = "OllamaModel"

    # Ollama API 返回的 JSON 数据中模型列表的键名
    JSON_MODELS_KEY = "models"
    # 模型名称字段的键名
    JSON_NAME_KEY = "name"
    # 模型能力列表字段的键名
    JSON_CAPABILITIES_KEY = "capabilities"
    # 所需的能力标识：文本补全
    DESIRED_CAPABILITY = "completion"
    # 工具调用能力标识
    TOOL_CALLING_CAPABILITY = "tools"

    # 格式化输出的表格列定义 schema，用于结构化输出字段的配置
    TABLE_SCHEMA = [
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
            "edit_mode": EditMode.INLINE,
            "options": ["True", "False"],
            "default": "False",
        },
    ]
    # 根据 TABLE_SCHEMA 生成默认行数据，每个字段取其默认值
    default_table_row = {row["name"]: row.get("default", None) for row in TABLE_SCHEMA}
    # 将默认行数据转换为 JSON Schema，用于检测用户是否修改了默认值
    default_table_row_schema = build_model_from_schema([default_table_row]).model_json_schema()

    # 组件输入参数定义
    inputs = [
        # Ollama API 地址，默认为本地 11434 端口
        StrInput(
            name="base_url",
            display_name="Ollama API URL",
            info="Endpoint of the Ollama API. Defaults to http://localhost:11434.",
            value="http://localhost:11434",
            real_time_refresh=True,
        ),
        # 模型名称下拉选择，选项列表从 Ollama API 动态获取
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            options=[],
            info="Refer to https://ollama.com/library for more models.",
            refresh_button=True,
            real_time_refresh=True,
            required=True,
        ),
        # Ollama API 密钥（可选），用于需要认证的 Ollama 部署
        SecretStrInput(
            name="api_key",
            display_name="Ollama API Key",
            info="Your Ollama API key.",
            value=None,
            required=False,
            real_time_refresh=True,
            advanced=True,
        ),
        # 温度参数，控制生成文本的随机性，值越高越随机
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            advanced=True,
        ),
        # 结构化输出格式配置表格，用于定义 JSON 输出的字段结构
        TableInput(
            name="format",
            display_name="Format",
            info="Specify the format of the output.",
            table_schema=TABLE_SCHEMA,
            value=default_table_row,
            show=False,
        ),
        # 运行追踪的元数据，会附加到调试和监控信息中
        DictInput(name="metadata", display_name="Metadata", info="Metadata to add to the run trace.", advanced=True),
        # Mirostat 采样算法选择，用于控制输出的困惑度
        DropdownInput(
            name="mirostat",
            display_name="Mirostat",
            options=["Disabled", "Mirostat", "Mirostat 2.0"],
            info="Enable/disable Mirostat sampling for controlling perplexity.",
            value="Disabled",
            advanced=True,
            real_time_refresh=True,
        ),
        # Mirostat 算法学习率参数
        FloatInput(
            name="mirostat_eta",
            display_name="Mirostat Eta",
            info="Learning rate for Mirostat algorithm. (Default: 0.1)",
            advanced=True,
        ),
        # Mirostat 算法平衡参数，控制输出连贯性与多样性的平衡
        FloatInput(
            name="mirostat_tau",
            display_name="Mirostat Tau",
            info="Controls the balance between coherence and diversity of the output. (Default: 5.0)",
            advanced=True,
        ),
        # 上下文窗口大小，决定模型一次能看到多少 token
        IntInput(
            name="num_ctx",
            display_name="Context Window Size",
            info="Size of the context window for generating tokens. (Default: 2048)",
            advanced=True,
        ),
        # 使用的 GPU 数量
        IntInput(
            name="num_gpu",
            display_name="Number of GPUs",
            info="Number of GPUs to use for computation. (Default: 1 on macOS, 0 to disable)",
            advanced=True,
        ),
        # 计算时使用的线程数
        IntInput(
            name="num_thread",
            display_name="Number of Threads",
            info="Number of threads to use during computation. (Default: detected for optimal performance)",
            advanced=True,
        ),
        # 重复惩罚的回溯范围，防止模型重复生成相同内容
        IntInput(
            name="repeat_last_n",
            display_name="Repeat Last N",
            info="How far back the model looks to prevent repetition. (Default: 64, 0 = disabled, -1 = num_ctx)",
            advanced=True,
        ),
        # 重复惩罚系数，值越大对重复内容的惩罚越重
        FloatInput(
            name="repeat_penalty",
            display_name="Repeat Penalty",
            info="Penalty for repetitions in generated text. (Default: 1.1)",
            advanced=True,
        ),
        # 尾部自由采样参数，用于提升生成质量
        FloatInput(name="tfs_z", display_name="TFS Z", info="Tail free sampling value. (Default: 1)", advanced=True),
        # 请求超时时间（秒）
        IntInput(name="timeout", display_name="Timeout", info="Timeout for the request stream.", advanced=True),
        # Top-K 采样，限制只从概率最高的 K 个 token 中选择
        IntInput(
            name="top_k", display_name="Top K", info="Limits token selection to top K. (Default: 40)", advanced=True
        ),
        # Top-P 核采样，与 Top-K 配合使用，控制采样范围
        FloatInput(name="top_p", display_name="Top P", info="Works together with top-k. (Default: 0.9)", advanced=True),
        # 是否启用详细输出，会打印响应文本
        BoolInput(
            name="enable_verbose_output",
            display_name="Ollama Verbose Output",
            info="Whether to print out response text.",
            advanced=True,
        ),
        # 运行追踪标签，逗号分隔，用于分类和过滤追踪记录
        MessageTextInput(
            name="tags",
            display_name="Tags",
            info="Comma-separated list of tags to add to the run trace.",
            advanced=True,
        ),
        # 停止 token 列表，遇到这些 token 时模型停止生成
        MessageTextInput(
            name="stop_tokens",
            display_name="Stop Tokens",
            info="Comma-separated list of tokens to signal the model to stop generating text.",
            advanced=True,
        ),
        # 系统提示词，用于定义模型的角色和行为
        MessageTextInput(
            name="system", display_name="System", info="System to use for generating text.", advanced=True
        ),
        # 是否启用工具调用（函数调用）能力
        BoolInput(
            name="tool_model_enabled",
            display_name="Tool Model Enabled",
            info="Whether to enable tool calling in the model.",
            value=True,
            real_time_refresh=True,
        ),
        # 自定义提示词模板
        MessageTextInput(
            name="template", display_name="Template", info="Template to use for generating text.", advanced=True
        ),
        # 是否启用结构化输出（JSON Schema 格式）
        BoolInput(
            name="enable_structured_output",
            display_name="Enable Structured Output",
            info="Whether to enable structured output in the model.",
            value=False,
            advanced=False,
            real_time_refresh=True,
        ),
        # 继承基础模型组件的通用输入参数（如流式输出、最大 token 数等）
        *LCModelComponent.get_base_inputs(),
    ]

    # 组件输出定义：文本输出、模型实例输出、JSON 数据输出、表格输出
    outputs = [
        Output(display_name="Text", name="text_output", method="text_response"),
        Output(display_name="Language Model", name="model_output", method="build_model"),
        Output(display_name="JSON", name="data_output", method="build_data_output"),
        Output(display_name="Table", name="dataframe_output", method="build_dataframe_output"),
    ]

    # 构建 LangChain ChatOllama 模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        # Mirostat 采样算法选项映射：1 表示 Mirostat 1.0，2 表示 Mirostat 2.0
        mirostat_options = {"Mirostat": 1, "Mirostat 2.0": 2}

        # 禁用时默认为 None
        mirostat_value = mirostat_options.get(self.mirostat, None)

        # 当 Mirostat 禁用时，将相关参数设为 None
        if mirostat_value is None:
            mirostat_eta = None
            mirostat_tau = None
        else:
            mirostat_eta = self.mirostat_eta
            mirostat_tau = self.mirostat_tau

        # 转换 localhost URL 以适配不同运行环境（如 Docker 容器）
        transformed_base_url = transform_localhost_url(self.base_url)

        # 检测 URL 是否包含 /v1 后缀（OpenAI 兼容模式），Ollama 原生 API 不需要此后缀
        if transformed_base_url and transformed_base_url.rstrip("/").endswith("/v1"):
            # 移除 /v1 后缀并记录警告日志
            transformed_base_url = transformed_base_url.rstrip("/").removesuffix("/v1")
            logger.warning(
                "Detected '/v1' suffix in base URL. The Ollama component uses the native Ollama API, "
                "not the OpenAI-compatible API. The '/v1' suffix has been automatically removed. "
                "If you want to use the OpenAI-compatible API, please use the OpenAI component instead. "
                "Learn more at https://docs.ollama.com/openai#openai-compatibility"
            )

        # 解析格式化输出的 JSON Schema（仅在启用结构化输出时）
        try:
            output_format = self._parse_format_field(self.format) if self.enable_structured_output else None
        except Exception as e:
            msg = f"Failed to parse the format field: {e}"
            raise ValueError(msg) from e

        # 构建传递给 ChatOllama 的所有参数字典
        llm_params = {
            "base_url": transformed_base_url,
            "model": self.model_name,
            "mirostat": mirostat_value,
            "format": output_format or None,
            "metadata": self.metadata,
            "tags": self.tags.split(",") if self.tags else None,
            "mirostat_eta": mirostat_eta,
            "mirostat_tau": mirostat_tau,
            "num_ctx": self.num_ctx or None,
            "num_gpu": self.num_gpu or None,
            "num_thread": self.num_thread or None,
            "repeat_last_n": self.repeat_last_n or None,
            "repeat_penalty": self.repeat_penalty or None,
            "temperature": self.temperature or None,
            "stop": self.stop_tokens.split(",") if self.stop_tokens else None,
            "system": self.system,
            "tfs_z": self.tfs_z or None,
            "timeout": self.timeout or None,
            "top_k": self.top_k or None,
            "top_p": self.top_p or None,
            "verbose": self.enable_verbose_output or False,
            "template": self.template,
        }
        # 如果配置了 API 密钥，将其作为请求头传递
        headers = self.headers
        if headers is not None:
            llm_params["client_kwargs"] = {"headers": headers}

        # 移除值为 None 的参数，避免传递无效参数给 ChatOllama
        llm_params = {k: v for k, v in llm_params.items() if v is not None}

        # 使用构建好的参数创建 ChatOllama 模型实例
        try:
            output = ChatOllama(**llm_params)
        except Exception as e:
            msg = (
                "Unable to connect to the Ollama API. "
                "Please verify the base URL, ensure the relevant Ollama model is pulled, and try again."
            )
            raise ValueError(msg) from e

        return output

    # 验证 Ollama API 地址是否有效，通过调用 /api/tags 端点进行检测
    async def is_valid_ollama_url(self, url: str) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                # 转换 localhost URL 以适配不同运行环境
                url = transform_localhost_url(url)
                if not url:
                    return False
                # 移除 /v1 后缀，因为 Ollama API 端点在根路径下
                url = url.rstrip("/").removesuffix("/v1")
                if not url.endswith("/"):
                    url = url + "/"
                # 请求 /api/tags 端点验证 URL 是否可达
                return (
                    await client.get(url=urljoin(url, "api/tags"), headers=self.headers)
                ).status_code == HTTP_STATUS_OK
        except httpx.RequestError:
            return False

    # 动态更新组件的构建配置，响应用户在画布上修改字段值的操作
    async def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None):
        # 结构化输出开关控制格式表格的显示/隐藏
        if field_name == "enable_structured_output":
            build_config["format"]["show"] = field_value

        # Mirostat 采样模式切换时，自动设置对应的 eta 和 tau 参数
        if field_name == "mirostat":
            if field_value == "Disabled":
                # 禁用时隐藏并清空相关参数
                build_config["mirostat_eta"]["advanced"] = True
                build_config["mirostat_tau"]["advanced"] = True
                build_config["mirostat_eta"]["value"] = None
                build_config["mirostat_tau"]["value"] = None

            else:
                # 启用时显示相关参数并设置默认值
                build_config["mirostat_eta"]["advanced"] = False
                build_config["mirostat_tau"]["advanced"] = False

                if field_value == "Mirostat 2.0":
                    build_config["mirostat_eta"]["value"] = 0.2
                    build_config["mirostat_tau"]["value"] = 10
                else:
                    build_config["mirostat_eta"]["value"] = 0.1
                    build_config["mirostat_tau"]["value"] = 5

        # 当模型名称、API 地址或工具调用开关变化时，重新获取可用模型列表
        if field_name in {"model_name", "base_url", "tool_model_enabled"}:
            # 如果正在更新 base_url 则使用新值，否则使用当前配置的值
            base_url_to_check = field_value if field_name == "base_url" else self.base_url
            # 如果字段值为空，回退到当前配置的 base_url
            if not base_url_to_check and field_name == "base_url":
                base_url_to_check = self.base_url
            logger.warning(f"Fetching Ollama models from updated URL: {base_url_to_check}")

            # 验证 URL 有效后，从 Ollama API 获取可用模型列表
            if base_url_to_check and await self.is_valid_ollama_url(base_url_to_check):
                tool_model_enabled = build_config["tool_model_enabled"].get("value", False) or self.tool_model_enabled
                build_config["model_name"]["options"] = await self.get_models(
                    base_url_to_check, tool_model_enabled=tool_model_enabled
                )
            else:
                build_config["name"]["options"] = []
        # Keep Alive 模式切换时，设置对应的超时值
        if field_name == "keep_alive_flag":
            if field_value == "Keep":
                # 保持连接：超时值设为 -1（永不超时）
                build_config["keep_alive"]["value"] = "-1"
                build_config["keep_alive"]["advanced"] = True
            elif field_value == "Immediately":
                # 立即释放：超时值设为 0
                build_config["keep_alive"]["value"] = "0"
                build_config["keep_alive"]["advanced"] = True
            else:
                # 自定义模式：显示超时值输入框
                build_config["keep_alive"]["advanced"] = False

        return build_config

    # 从 Ollama API 获取适用于文本生成的模型列表
    async def get_models(self, base_url_value: str, *, tool_model_enabled: bool | None = None) -> list[str]:
        """Fetches a list of models from the Ollama API suitable for text generation.

        Args:
            base_url_value (str): The base URL of the Ollama API.
            tool_model_enabled (bool | None, optional): If True, filters the models further to include
                only those that support tool calling. Defaults to None.

        Returns:
            list[str]: A list of model names suitable for text generation. Models are included if:
                - They have the "completion" capability, OR
                - The capabilities field is not returned (backwards compatibility with older Ollama versions)
                If `tool_model_enabled` is True, only models with verified "tools" capability are included
                (models without capabilities info are excluded in this case).

        Raises:
            ValueError: If there is an issue with the API request or response, or if the model
                names cannot be retrieved.
        """
        try:
            # 移除 /v1 后缀并转换 localhost URL
            base_url = base_url_value.rstrip("/").removesuffix("/v1")
            if not base_url.endswith("/"):
                base_url = base_url + "/"
            base_url = transform_localhost_url(base_url)

            # Ollama REST API：获取已安装模型列表的端点
            tags_url = urljoin(base_url, "api/tags")

            # Ollama REST API：获取模型详细信息（含能力列表）的端点
            show_url = urljoin(base_url, "api/show")

            async with httpx.AsyncClient() as client:
                headers = self.headers
                # 请求模型列表
                tags_response = await client.get(url=tags_url, headers=headers)
                tags_response.raise_for_status()
                models = tags_response.json()
                if asyncio.iscoroutine(models):
                    models = await models
                await logger.adebug(f"Available models: {models}")

                # 遍历所有模型，过滤出适合文本生成的模型（非嵌入模型）
                model_ids = []
                for model in models[self.JSON_MODELS_KEY]:
                    model_name = model[self.JSON_NAME_KEY]
                    await logger.adebug(f"Checking model: {model_name}")

                    # 查询每个模型的详细能力信息
                    payload = {"model": model_name}
                    show_response = await client.post(url=show_url, json=payload, headers=headers)
                    show_response.raise_for_status()
                    json_data = show_response.json()
                    if asyncio.iscoroutine(json_data):
                        json_data = await json_data

                    capabilities = json_data.get(self.JSON_CAPABILITIES_KEY)
                    await logger.adebug(f"Model: {model_name}, Capabilities: {capabilities}")

                    # 如果未返回能力信息，假定为补全模型（兼容旧版 Ollama）
                    # 旧版 Ollama 的 /api/show 端点不返回 capabilities 字段
                    if capabilities is None:
                        if not tool_model_enabled:
                            model_ids.append(model_name)
                        # 启用工具调用模式时，跳过无能力信息的模型（无法验证工具支持）
                    # 筛选具有补全能力的模型，若启用工具调用则还需具备 tools 能力
                    elif self.DESIRED_CAPABILITY in capabilities and (
                        not tool_model_enabled or self.TOOL_CALLING_CAPABILITY in capabilities
                    ):
                        model_ids.append(model_name)

        except (httpx.RequestError, ValueError) as e:
            msg = "Could not get model names from Ollama."
            raise ValueError(msg) from e

        return model_ids

    # 解析格式化输出字段，支持字符串、JSON 字符串和字典等多种输入格式
    def _parse_format_field(self, format_value: Any) -> Any:
        """Parse the format field to handle both string and dict inputs.

        The format field can be:
        - A simple string like "json" (backward compatibility)
        - A JSON string from NestedDictInput that needs parsing
        - A dict/JSON schema (already parsed)
        - None or empty

        Args:
            format_value: The raw format value from the input field

        Returns:
            Parsed format value as string, dict, or None
        """
        # 空值直接返回 None
        if not format_value:
            return None

        schema = format_value
        # 列表类型：将表格行数据转换为 JSON Schema
        if isinstance(format_value, list):
            schema = build_model_from_schema(format_value).model_json_schema()
            # 如果转换后的 schema 与默认占位行相同，说明用户未修改，返回 None
            if schema == self.default_table_row_schema:
                return None  # the rows are generic placeholder rows
        # 字符串类型：尝试解析为 JSON（如 "json" 或 JSON 字符串）
        elif isinstance(format_value, str):  # parse as json if string
            with suppress(json.JSONDecodeError):  # e.g., literal "json" is valid for format field
                schema = json.loads(format_value)

        return schema or None

    # 解析模型返回的 JSON 响应，用于结构化输出场景
    async def _parse_json_response(self) -> Any:
        """Parse the JSON response from the model.

        This method gets the text response and attempts to parse it as JSON.
        Works with models that have format='json' or a JSON schema set.

        Returns:
            Parsed JSON (dict, list, or primitive type)

        Raises:
            ValueError: If the response is not valid JSON
        """
        # 获取文本响应内容
        message = await self.text_response()
        text = message.text if hasattr(message, "text") else str(message)

        # 空响应时报错
        if not text:
            msg = "No response from model"
            raise ValueError(msg)

        # 尝试将文本解析为 JSON 对象
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON response. Ensure model supports JSON output. Error: {e}"
            raise ValueError(msg) from e

    # 将模型的 JSON 响应转换为 Data 输出对象
    async def build_data_output(self) -> Data:
        """Build a Data output from the model's JSON response.

        Returns:
            Data: A Data object containing the parsed JSON response
        """
        parsed = await self._parse_json_response()

        # 字典类型直接包装为 Data 对象
        if isinstance(parsed, dict):
            return Data(data=parsed)

        # 列表类型：单元素列表直接取第一个元素，多元素列表包装为 results
        if isinstance(parsed, list):
            if len(parsed) == 1:
                return Data(data=parsed[0])
            return Data(data={"results": parsed})

        # 基本类型（str、int、float、bool）包装为 value 容器
        return Data(data={"value": parsed})

    async def build_dataframe_output(self) -> DataFrame:
        """Build a DataFrame output from the model's JSON response.

        Returns:
            DataFrame: A DataFrame containing the parsed JSON response

        Raises:
            ValueError: If the response cannot be converted to a DataFrame
        """
        parsed = await self._parse_json_response()

        # If it's a list of dicts, convert directly to DataFrame
        if isinstance(parsed, list):
            if not parsed:
                return DataFrame()
            # Ensure all items are dicts for proper DataFrame conversion
            if all(isinstance(item, dict) for item in parsed):
                return DataFrame(parsed)
            msg = "List items must be dictionaries to convert to DataFrame"
            raise ValueError(msg)

        # If it's a single dict, wrap in a list to create a single-row DataFrame
        if isinstance(parsed, dict):
            return DataFrame([parsed])

        # For primitive types, create a single-column DataFrame
        return DataFrame([{"value": parsed}])

    @property
    def headers(self) -> dict[str, str] | None:
        """Get the headers for the Ollama API."""
        if self.api_key and self.api_key.strip():
            return {"Authorization": f"Bearer {self.api_key}"}
        return None
