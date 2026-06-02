# IO 模块：统一导出所有组件输入类型和输出模板
# 本模块从 lfx 包中重新导出所有内置的输入组件类型，
# 供 langflow-base 及上层模块使用，避免直接依赖 lfx 的内部路径。

from lfx.io import (
    BoolInput,  # 布尔类型输入（开关）
    CodeInput,  # 代码编辑器输入
    DataFrameInput,  # DataFrame 数据表格输入
    DataInput,  # 通用数据对象输入
    DefaultPromptField,  # 默认提示词字段（用于动态构建 Prompt）
    DictInput,  # 字典/键值对输入
    DropdownInput,  # 下拉选择框输入
    FileInput,  # 文件上传输入
    FloatInput,  # 浮点数输入
    HandleInput,  # 句柄输入（用于节点间连线传递引用）
    IntInput,  # 整数输入
    LinkInput,  # 链接/URL 输入
    McpInput,  # MCP 服务输入
    MessageInput,  # 消息对象输入
    MessageTextInput,  # 消息文本输入（纯文本形式的消息）
    MultilineInput,  # 多行文本输入
    MultilineSecretInput,  # 多行密钥/密码输入（内容隐藏）
    MultiselectInput,  # 多选输入
    NestedDictInput,  # 嵌套字典输入
    PromptInput,  # 提示词模板输入
    QueryInput,  # 查询语句输入
    SecretStrInput,  # 密钥字符串输入（内容隐藏）
    SliderInput,  # 滑块输入（用于范围选择）
    StrInput,  # 字符串输入
    TabInput,  # 标签页输入（用于分组展示）
    TableInput,  # 表格输入（结构化数据）
    ToolsInput,  # 工具/函数列表输入
)
from lfx.template import Output  # 输出模板定义，用于声明组件的输出端口

# 模块公开 API 列表，控制外部通过 from langflow.io import * 可导入的内容
__all__ = [
    "BoolInput",
    "CodeInput",
    "DataFrameInput",
    "DataInput",
    "DefaultPromptField",
    "DefaultPromptField",
    "DictInput",
    "DropdownInput",
    "FileInput",
    "FloatInput",
    "HandleInput",
    "IntInput",
    "LinkInput",
    "LinkInput",
    "McpInput",
    "MessageInput",
    "MessageTextInput",
    "MultilineInput",
    "MultilineSecretInput",
    "MultiselectInput",
    "NestedDictInput",
    "Output",
    "PromptInput",
    "QueryInput",
    "SecretStrInput",
    "SliderInput",
    "StrInput",
    "TabInput",
    "TableInput",
    "ToolsInput",
]
