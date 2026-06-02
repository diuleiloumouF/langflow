"""输入组件模块 - 提供所有组件可用的输入类型定义。

本模块从 lfx.inputs.inputs 重新导出所有输入类型，
供 langflow 平台层的组件使用。
"""

from lfx.inputs.inputs import (
    AuthInput,  # 认证输入，用于 API 密钥等认证信息
    BoolInput,  # 布尔输入，用于开关选项
    CodeInput,  # 代码输入，用于输入代码片段
    ConnectionInput,  # 连接输入，用于组件间的连接
    DataFrameInput,  # 数据框输入，用于表格数据
    DataInput,  # 数据输入，通用数据类型
    DefaultPromptField,  # 默认提示字段，用于提示词模板
    DictInput,  # 字典输入，用于键值对数据
    DropdownInput,  # 下拉框输入，用于从选项列表中选择
    FieldTypes,  # 字段类型枚举
    FileInput,  # 文件输入，用于文件上传
    FloatInput,  # 浮点数输入
    HandleInput,  # 句柄输入，用于组件输出连接
    Input,  # 基础输入类
    IntInput,  # 整数输入
    LinkInput,  # 链接输入，用于 URL 链接
    McpInput,  # MCP 输入，用于 MCP 协议交互
    MessageInput,  # 消息输入，用于聊天消息
    MessageTextInput,  # 消息文本输入，用于纯文本消息
    ModelInput,  # 模型输入，用于选择 AI 模型
    MultilineInput,  # 多行文本输入
    MultilineSecretInput,  # 多行密钥输入，用于敏感多行文本
    MultiselectInput,  # 多选输入，用于多选项
    NestedDictInput,  # 嵌套字典输入，用于多层键值对
    PromptInput,  # 提示词输入，用于提示词模板
    QueryInput,  # 查询输入，用于搜索查询
    SecretStrInput,  # 密钥字符串输入，用于敏感信息
    SliderInput,  # 滑块输入，用于数值范围选择
    SortableListInput,  # 可排序列表输入
    StrInput,  # 字符串输入
    TabInput,  # 标签页输入，用于多标签切换
    TableInput,  # 表格输入，用于结构化数据
    ToolsInput,  # 工具输入，用于选择工具
)

# 模块公开的 API 列表，定义了通过 from langflow.inputs import * 可导入的所有名称
__all__ = [
    "AuthInput",
    "BoolInput",
    "CodeInput",
    "ConnectionInput",
    "DataFrameInput",
    "DataInput",
    "DefaultPromptField",
    "DictInput",
    "DropdownInput",
    "FieldTypes",
    "FileInput",
    "FloatInput",
    "HandleInput",
    "Input",
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
    "SortableListInput",
    "StrInput",
    "TabInput",
    "TableInput",
    "ToolsInput",
]
