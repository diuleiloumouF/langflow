"""SemanticMap component for transforming each row of input data using LLM-based semantic processing."""
# SemanticMap 组件，使用基于 LLM 的语义处理来转换输入数据的每一行

from __future__ import annotations

from typing import ClassVar

from pydantic import create_model

from lfx.components.agentics.constants import (
    ERROR_AGENTICS_NOT_INSTALLED,
    ERROR_INPUT_SCHEMA_REQUIRED,
    TRANSDUCTION_AMAP,
)
from lfx.components.agentics.helpers import (
    build_schema_fields,
    prepare_llm_from_component,
)
from lfx.components.agentics.inputs import (
    get_generated_fields_input,
    get_model_provider_inputs,
)
from lfx.components.agentics.inputs.base_component import BaseAgenticComponent
from lfx.io import (
    BoolInput,
    DataFrameInput,
    MessageTextInput,
    Output,
)
from lfx.schema.dataframe import DataFrame


# AMapComponent: 语义映射组件，使用自然语言指令和预定义输出模式逐行转换输入数据
# 通过 LLM 对每一行数据进行独立处理，生成新的列或从每条记录中提取洞察
class AMapComponent(BaseAgenticComponent):
    """Transform each row of input data using natural language instructions and a defined output schema.

    This component processes input data row-by-row, applying LLM-based transformations to generate
    new columns or derive insights for each individual record.
    """

    # 基础继承类名，用于代码生成时引用
    code_class_base_inheritance: ClassVar[str] = "Component"
    # 组件显示名称
    display_name = "aMap"
    # 组件描述，说明其功能为基于输入模式增强数据框并添加新列，使用 LLM 并行处理行
    description = (
        "Augment the input dataframe adding new columns defined in the input schema. "
        "Rows are processed independently and in parallel using LLMs."
    )
    # 组件文档链接
    documentation: str = "https://docs.langflow.org/bundles-agentics"
    # 组件图标标识
    icon = "Agentics"

    # 组件输入定义列表
    inputs = [
        # 模型提供商相关输入（如 LLM 模型选择等），展开合并到此列表
        *get_model_provider_inputs(),
        # 输入数据表：要转换的 DataFrame，模式会自动从列名和类型推断
        DataFrameInput(
            name="source",
            display_name="Input Table",
            info=("Input DataFrame to transform. The schema is automatically inferred from column names and types."),
            required=True,
        ),
        # 生成字段输入：定义输出模式的字段
        get_generated_fields_input(),
        # 是否返回多实例：为 True 时，为每个输入行生成模式的多个实例并拼接
        BoolInput(
            name="return_multiple_instances",
            display_name="As List",
            info=(
                "If True, generate multiple instances of the provided schema for each input row concatenating all them."
            ),
            advanced=False,
            value=False,
        ),
        # 自然语言指令：描述如何将每个输入行转换为输出模式
        MessageTextInput(
            name="instructions",
            display_name="Instructions",
            info="Natural language instructions describing how to transform each input row into the output schema.",
            value="",
            required=False,
        ),
        # 是否保留源列：保留原始输入列到输出中；若禁用则只返回新生成的列（在 As List 为 True 时忽略此设置）
        BoolInput(
            name="append_to_input_columns",
            display_name="Keep Source Columns",
            info=(
                "Keep original input columns in the output. If disabled, only newly "
                "generated columns are returned. This is ignored if As List is set to True."
            ),
            value=True,
            advanced=True,
        ),
    ]

    # 组件输出定义列表
    outputs = [
        # 输出表：语义映射转换后的 DataFrame
        Output(
            name="states",
            display_name="Output Table",
            info="Transformed DataFrame resulting from semantic mapping.",
            method="aMap",
            tool_mode=True,
        ),
    ]

    async def aMap(self) -> DataFrame:  # noqa: N802
        """Transform input data row-by-row using LLM-based semantic processing.

        Returns:
            DataFrame with transformed data following the output schema.
        """
        # 动态导入 agentics 库，仅在运行时加载
        try:
            from agentics import AG
            from agentics.core.atype import create_pydantic_model
        except ImportError as e:
            # agentics 未安装时抛出导入错误
            raise ImportError(ERROR_AGENTICS_NOT_INSTALLED) from e

        # 从组件配置准备 LLM 实例
        llm = prepare_llm_from_component(self)
        # 校验输入数据和模式不为空
        if self.source and self.schema != []:
            # 将输入 DataFrame 包装为 AG 对象（agentics 核心数据结构）
            source = AG.from_dataframe(DataFrame(self.source))

            # 根据用户定义的模式字段构建目标 Pydantic 模型
            schema_fields = build_schema_fields(self.schema)
            atype = create_pydantic_model(schema_fields, name="Target")
            # 如果需要返回多实例模式，将目标类型包装为列表类型
            if self.return_multiple_instances:
                final_atype = create_model("ListOfTarget", items=(list[atype], ...))  # type: ignore[valid-type]
            else:
                final_atype = atype

            # 创建目标 AG 对象，指定类型、转换方式和 LLM
            target = AG(
                atype=final_atype,
                transduction_type=TRANSDUCTION_AMAP,
                llm=llm,
            )
            # 根据指令格式设置提示模板或追加指令文本
            if "{" in self.instructions:
                # 指令中包含花括号，视为模板格式，直接设置为提示模板
                source.prompt_template = self.instructions
            else:
                # 指令为纯文本，追加到现有指令列表
                source.instructions += self.instructions

            # 执行语义映射转换：通过 << 操作符将源数据转换为目标模式
            output = await (target << source)
            # 多实例模式：将所有行的实例扁平化为一个 AG 对象
            if self.return_multiple_instances:
                appended_states = [item_state for state in output for item_state in state.items]
                output = AG(atype=atype, states=appended_states)

            # 非多实例模式下，如果需要保留源列，则合并源数据和输出数据
            elif self.append_to_input_columns:
                # 获取输出和源的字段名集合，检测是否有重叠
                output_field_names = set(output.atype.model_fields.keys())
                source_field_names = set(source.atype.model_fields.keys())
                overlapping = source_field_names & output_field_names
                if overlapping:
                    # 移除源中与输出重叠的字段，避免合并时冲突
                    non_overlapping = source_field_names - overlapping
                    deduplicated_atype = source.subset_atype(non_overlapping)
                    source = source.rebind_atype(deduplicated_atype)
                # 将源数据状态合并到输出数据中
                output = source.merge_states(output)

            # 将 AG 结果转换为 DataFrame 并返回
            return DataFrame(output.to_dataframe().to_dict(orient="records"))
        # 如果输入数据或模式为空，抛出值错误
        raise ValueError(ERROR_INPUT_SCHEMA_REQUIRED)
