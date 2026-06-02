"""Re-export of all input classes from lfx.

This module maintains backward compatibility by re-exporting all input classes from lfx.
All input classes have been migrated to lfx and this file serves as a compatibility layer.
"""

# 从 lfx 包重新导出所有输入类，保持 langflow-base 包的向后兼容性。
# 所有输入类已迁移至 lfx 包，本文件仅作为兼容层存在。
from lfx.inputs.inputs import (
    AuthInput,  # 认证输入
    BoolInput,  # 布尔值输入（True/False 开关）
    CodeInput,  # 代码输入（支持代码编辑的多行文本）
    DataFrameInput,  # 数据框输入（DataFrame 类型数据）
    DataInput,  # 通用数据输入
    DefaultPromptField,  # 默认提示词字段（用于构建提示模板）
    DictInput,  # 字典输入（键值对结构）
    DropdownInput,  # 下拉选择输入（从预设选项中选择）
    FileInput,  # 文件上传输入
    FloatInput,  # 浮点数输入
    HandleInput,  # 连接句柄输入（用于组件间的数据连线）
    InputTypes,  # 输入类型枚举/集合
    InputTypesMap,  # 输入类型映射表（输入类型名称到类的映射）
    IntInput,  # 整数输入
    LinkInput,  # 链接输入（URL 地址）
    McpInput,  # MCP（Model Context Protocol）输入
    MessageInput,  # 消息输入（Message 对象类型）
    MessageTextInput,  # 消息文本输入（字符串形式的消息内容）
    ModelInput,  # 模型选择输入（用于选择 LLM 模型）
    MultilineInput,  # 多行文本输入
    MultilineSecretInput,  # 多行密钥输入（敏感信息，内容隐藏显示）
    MultiselectInput,  # 多选输入（可选择多个预设选项）
    NestedDictInput,  # 嵌套字典输入（支持多层嵌套的键值对）
    PromptInput,  # 提示词输入（用于编辑提示模板）
    QueryInput,  # 查询输入
    SecretStrInput,  # 密钥字符串输入（敏感信息，内容隐藏显示）
    SliderInput,  # 滑块输入（在范围内选择数值）
    StrInput,  # 字符串输入（单行文本）
    TabInput,  # 标签页输入（用于切换不同输入面板）
    TableInput,  # 表格输入（结构化表格数据）
    ToolsInput,  # 工具输入（Agent 可使用的工具列表）
    instantiate_input,  # 工具函数：根据输入类型名称实例化对应的输入对象
)

__all__ = [
    "AuthInput",
    "BoolInput",
    "CodeInput",
    "DataFrameInput",
    "DataInput",
    "DefaultPromptField",
    "DictInput",
    "DropdownInput",
    "FileInput",
    "FloatInput",
    "HandleInput",
    "InputTypes",
    "InputTypesMap",
    "IntInput",
    "LinkInput",
    "McpInput",
    "MessageInput",
    "MessageTextInput",
    "ModelInput",
    "MultilineInput",
    "MultilineSecretInput",
    "MultiselectInput",
    "NestedDictInput",
    "PromptInput",
    "QueryInput",
    "SecretStrInput",
    "SliderInput",
    "StrInput",
    "TabInput",
    "TableInput",
    "ToolsInput",
    "instantiate_input",
]
