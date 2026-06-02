# 正则表达式模块
import re

# 组件基类
from lfx.custom.custom_component.component import Component

# 输入输出类型定义
from lfx.field_typing import Input, Output, Text


# 代码块提取组件，从文本中提取代码块
class CodeBlockExtractor(Component):
    display_name = "Code Block Extractor"
    description = "Extracts code block from text."
    name = "CodeBlockExtractor"

    # 输入参数定义
    inputs = [Input(name="text", field_type=Text, description="Text to extract code blocks from.")]

    # 输出参数定义
    outputs = [Output(name="code_block", display_name="Code Block", method="get_code_block")]

    # 从文本中提取代码块
    def get_code_block(self) -> Text:
        text = self.text.strip()
        # 使用正则表达式提取代码块
        # 代码块可能以 ``` 或 ```language 开始
        # 代码块以 ``` 结束
        pattern = r"^```(?:\w+)?\s*\n(.*?)(?=^```)```"
        match = re.search(pattern, text, re.MULTILINE)
        code_block = ""
        if match:
            code_block = match.group(1)
        return code_block
