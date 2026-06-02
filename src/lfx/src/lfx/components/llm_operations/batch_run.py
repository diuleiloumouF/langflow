# 批量运行 LLM 组件 —— 对 DataFrame 的每一行调用大语言模型并返回结果
from __future__ import annotations

from typing import Any, cast

import toml  # type: ignore[import-untyped]

from lfx.base.models.unified_models import (
    get_llm,
    handle_model_input_update,
)
from lfx.base.models.watsonx_constants import IBM_WATSONX_URLS
from lfx.custom.custom_component.component import Component
from lfx.io import (
    BoolInput,
    DataFrameInput,
    DropdownInput,
    MessageTextInput,
    ModelInput,
    MultilineInput,
    Output,
    SecretStrInput,
    StrInput,
)
from lfx.log.logger import logger
from lfx.schema.dataframe import DataFrame
from lfx.schema.token_usage import accumulate_usage, extract_usage_from_message


class BatchRunComponent(Component):
    """批量运行组件 —— 对 DataFrame 的每一行调用 LLM，将模型响应作为新列添加到结果中。"""

    display_name = "Batch Run"
    description = "Runs an LLM on each row of a DataFrame column. If no column is specified, all columns are used."
    documentation: str = "https://docs.langflow.org/batch-run"
    icon = "List"

    # 组件输入定义：语言模型、API Key、watsonx 配置、系统指令、输入表格、列名、输出列名、元数据开关
    inputs = [
        # 语言模型选择器
        ModelInput(
            name="model",
            display_name="Language Model",
            info="Select your model provider",
            real_time_refresh=True,
            required=True,
        ),
        # API Key 输入（可选，覆盖全局配置）
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            info="Overrides global provider settings. Leave blank to use your pre-configured API Key.",
            real_time_refresh=True,
            advanced=True,
        ),
        # IBM watsonx API 端点下拉框（默认隐藏，仅 watsonx 模型显示）
        DropdownInput(
            name="base_url_ibm_watsonx",
            display_name="watsonx API Endpoint",
            info="The base URL of the API (IBM watsonx.ai only)",
            options=IBM_WATSONX_URLS,
            value=IBM_WATSONX_URLS[0],
            show=False,
            real_time_refresh=True,
        ),
        # IBM watsonx 项目 ID（默认隐藏）
        StrInput(
            name="project_id",
            display_name="watsonx Project ID",
            info="The project ID associated with the foundation model (IBM watsonx.ai only)",
            show=False,
            required=False,
        ),
        # 系统指令，将作为 system message 应用到每一行
        MultilineInput(
            name="system_message",
            display_name="Instructions",
            info="Multi-line system instruction for all rows in the DataFrame.",
            required=False,
        ),
        # 输入的 DataFrame 表格
        DataFrameInput(
            name="df",
            display_name="Table",
            info="The DataFrame whose column (specified by 'column_name') we'll treat as text messages.",
            required=True,
        ),
        # 指定作为文本输入的列名，为空则将整行格式化为 TOML
        MessageTextInput(
            name="column_name",
            display_name="Column Name",
            info=(
                "The name of the DataFrame column to treat as text messages. "
                "If empty, all columns will be formatted in TOML."
            ),
            required=False,
            advanced=False,
        ),
        # 输出列名，模型响应将存储在此列中
        MessageTextInput(
            name="output_column_name",
            display_name="Output Column Name",
            info="Name of the column where the model's response will be stored.",
            value="model_response",
            required=False,
            advanced=True,
        ),
        # 是否在输出中包含元数据信息
        BoolInput(
            name="enable_metadata",
            display_name="Enable Metadata",
            info="If True, add metadata to the output DataFrame.",
            value=False,
            required=False,
            advanced=True,
        ),
    ]

    # 组件输出定义：包含原始列和模型响应列的 DataFrame
    outputs = [
        Output(
            display_name="LLM Results",
            name="batch_results",
            method="run_batch",
            info="A DataFrame with all original columns plus the model's response column.",
        ),
    ]

    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        # 动态更新构建配置，根据用户选择的模型提供商过滤可用选项
        """Dynamically update build config with user-filtered model options."""
        return handle_model_input_update(self, build_config, field_value, field_name)

    def _format_row_as_toml(self, row: dict[str, Any]) -> str:
        # 将字典（DataFrame 的一行）转换为 TOML 格式字符串
        """Convert a dictionary (row) into a TOML-formatted string."""
        formatted_dict = {str(col): {"value": str(val)} for col, val in row.items()}
        return toml.dumps(formatted_dict)

    def _create_base_row(
        self, original_row: dict[str, Any], model_response: str = "", batch_index: int = -1
    ) -> dict[str, Any]:
        # 创建基础输出行：复制原始数据，附加模型响应和批处理索引
        """Create a base row with original columns and additional metadata."""
        row = original_row.copy()
        row[self.output_column_name] = model_response
        row["batch_index"] = batch_index
        return row

    def _add_metadata(
        self, row: dict[str, Any], *, success: bool = True, system_msg: str = "", error: str | None = None
    ) -> None:
        # 如果启用了元数据，为该行添加处理状态、输入输出长度等元信息
        """Add metadata to a row if enabled."""
        if not self.enable_metadata:
            return

        if success:
            row["metadata"] = {
                "has_system_message": bool(system_msg),
                "input_length": len(row.get("text_input", "")),
                "response_length": len(row[self.output_column_name]),
                "processing_status": "success",
            }
        else:
            row["metadata"] = {
                "error": error,
                "processing_status": "failed",
            }

    async def run_batch(self) -> DataFrame:
        # 批量处理入口：对 DataFrame 的每一行异步调用 LLM 并返回包含响应的新 DataFrame
        """Process each row in df[column_name] with the language model asynchronously."""
        # 检查模型是实例还是列表（列表时需要实例化，实例时通常是在测试中）
        # Check if model is already an instance (for testing) or needs to be instantiated
        if isinstance(self.model, list):
            model = get_llm(
                model=self.model,
                user_id=self.user_id,
                api_key=self.api_key,
                watsonx_url=getattr(self, "base_url_ibm_watsonx", None),
                watsonx_project_id=getattr(self, "project_id", None),
            )
        else:
            # 模型已经是实例（通常在测试中）
            # Model is already an instance (typically in tests)
            model = self.model

        system_msg = self.system_message or ""
        df: DataFrame = self.df
        col_name = self.column_name or ""

        # 输入校验
        # Validate inputs first
        if not isinstance(df, DataFrame):
            msg = f"Expected DataFrame input, got {type(df)}"
            raise TypeError(msg)

        if col_name and col_name not in df.columns:
            msg = f"Column '{col_name}' not found in the DataFrame. Available columns: {', '.join(df.columns)}"
            raise ValueError(msg)

        try:
            # 确定每行的文本输入：指定了列名则取该列，否则将整行格式化为 TOML
            # Determine text input for each row
            if col_name:
                user_texts = df[col_name].astype(str).tolist()
            else:
                user_texts = [
                    self._format_row_as_toml(cast("dict[str, Any]", row)) for row in df.to_dict(orient="records")
                ]

            total_rows = len(user_texts)
            await logger.ainfo(f"Processing {total_rows} rows with batch run")

            # 构建对话列表：每条对话包含可选的 system message 和 user message
            # Prepare the batch of conversations
            conversations = [
                [{"role": "system", "content": system_msg}, {"role": "user", "content": text}]
                if system_msg
                else [{"role": "user", "content": text}]
                for text in user_texts
            ]

            # 为模型配置运行名称、项目名和回调函数
            # 某些模型（如 ChatWatsonx）可能因 SecretStr 等不可序列化属性导致 with_config() 出错
            # Configure the model with project info and callbacks
            # Some models (e.g., ChatWatsonx) may have serialization issues with with_config()
            # due to SecretStr or other non-serializable attributes
            try:
                model = model.with_config(
                    {
                        "run_name": self.display_name,
                        "project_name": self.get_project_name(),
                        "callbacks": self.get_langchain_callbacks(),
                    }
                )
            except (TypeError, ValueError, AttributeError) as e:
                # 配置失败时记录警告，继续无配置运行
                # Log warning and continue without configuration
                await logger.awarning(
                    f"Could not configure model with callbacks and project info: {e!s}. "
                    "Proceeding with batch processing without configuration."
                )
            # 批量调用模型并记录索引以便后续排序
            # Process batches and track progress
            responses_with_idx = list(
                zip(
                    range(len(conversations)),
                    await model.abatch(list(conversations)),
                    strict=True,
                )
            )

            # 按索引排序以保持原始顺序
            # Sort by index to maintain order
            responses_with_idx.sort(key=lambda x: x[0])

            # 组装最终输出：每行包含原始数据 + 模型响应 + 可选元数据
            # Build the final data with enhanced metadata
            rows: list[dict[str, Any]] = []
            for idx, (original_row, response) in enumerate(
                zip(df.to_dict(orient="records"), responses_with_idx, strict=False)
            ):
                response_msg = response[1]
                # 累计 token 使用量统计
                self._token_usage = accumulate_usage(self._token_usage, extract_usage_from_message(response_msg))
                response_text = response_msg.content if hasattr(response_msg, "content") else str(response_msg)
                row = self._create_base_row(
                    cast("dict[str, Any]", original_row), model_response=response_text, batch_index=idx
                )
                self._add_metadata(row, success=True, system_msg=system_msg)
                rows.append(row)

                # 每处理约 10% 的行记录一次进度日志
                # Log progress
                if (idx + 1) % max(1, total_rows // 10) == 0:
                    await logger.ainfo(f"Processed {idx + 1}/{total_rows} rows")

            await logger.ainfo("Batch processing completed successfully")
            return DataFrame(rows)

        except (KeyError, AttributeError) as e:
            # 捕获数据结构或属性访问错误，返回包含错误信息的单行 DataFrame
            # Handle data structure and attribute access errors
            await logger.aerror(f"Data processing error: {e!s}")
            error_row = self._create_base_row(dict.fromkeys(df.columns, ""), model_response="", batch_index=-1)
            self._add_metadata(error_row, success=False, error=str(e))
            return DataFrame([error_row])
