"""This module contains constants used in the Langflow base module.

Langflow 基础模块中使用的常量定义。

Constants:
- STREAM_INFO_TEXT: A string representing the information about streaming the response from the model.
  表示模型流式响应信息的字符串常量。
- NODE_FORMAT_ATTRIBUTES: A list of attributes used for formatting nodes.
  用于格式化节点的属性列表。
- FIELD_FORMAT_ATTRIBUTES: A list of attributes used for formatting fields.
  用于格式化字段的属性列表。
"""

import orjson

# 流式响应提示文本，提示用户该响应支持流式输出（仅在 Chat 模式下可用）
STREAM_INFO_TEXT = "Stream the response from the model. Streaming works only in Chat."

# 节点格式化属性列表，定义了节点在前端展示时需要格式化的属性
NODE_FORMAT_ATTRIBUTES = [
    "beta",
    "legacy",
    "icon",
    "output_types",
    "edited",
    "metadata",
    # remove display_name to prevent overwriting the display_name from the latest template
    # 移除 display_name 以避免覆盖最新模板中的 display_name
    # "display_name",
    "description",
]


# 字段格式化属性列表，定义了字段在前端展示时需要格式化的属性
FIELD_FORMAT_ATTRIBUTES = [
    "info",
    "display_name",
    "required",
    "list",
    "multiline",
    "combobox",
    "fileTypes",
    "password",
    "input_types",
    "title_case",
    "real_time_refresh",
    "refresh_button",
    "refresh_button_text",
    "options",
    "advanced",
    "copy_field",
]
# 需要跳过的字段属性列表，这些属性在格式化时会被忽略
SKIPPED_FIELD_ATTRIBUTES = ["advanced"]
# orjson 序列化选项：启用缩进、按键排序、忽略微秒精度
ORJSON_OPTIONS = orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS | orjson.OPT_OMIT_MICROSECONDS
# 需要跳过的组件集合，这些组件在某些处理流程中会被排除
SKIPPED_COMPONENTS = {"LanguageModelComponent"}
