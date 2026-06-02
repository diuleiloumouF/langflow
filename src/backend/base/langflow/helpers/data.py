# 正则表达式模块，用于字符串清理
import re

# defaultdict: 提供带默认值的字典，Any: 通用类型注解
from collections import defaultdict
from typing import Any

# orjson: 高性能 JSON 序列化库
import orjson

# jsonable_encoder: FastAPI 提供的编码器，将对象转换为 JSON 可序列化的格式
from fastapi.encoders import jsonable_encoder

# Document: LangChain 文档对象，表示一个带元数据的文本片段
from langchain_core.documents import Document

# Data: Langflow 数据模式对象，封装组件间传递的数据
from lfx.schema.data import Data

# DataFrame: Langflow 数据表模式对象，基于 pandas DataFrame
from lfx.schema.dataframe import DataFrame

# Message: Langflow 消息模式对象，表示聊天消息
from langflow.schema.message import Message


def docs_to_data(documents: list[Document]) -> list[Data]:
    """Converts a list of Documents to a list of Data.

    将 LangChain Document 列表转换为 Langflow Data 列表。

    Args:
        documents (list[Document]): The list of Documents to convert.
            要转换的 Document 列表。

    Returns:
        list[Data]: The converted list of Data.
            转换后的 Data 列表。
    """
    return [Data.from_document(document) for document in documents]


def data_to_text_list(template: str, data: Data | list[Data]) -> tuple[list[str], list[Data]]:
    """Format text from Data objects using a template string.

    使用模板字符串将 Data 对象格式化为文本列表。

    This function processes Data objects and formats their content using a template string.
    It handles various data structures and ensures consistent text formatting across different
    input types.

    Key Features:
    - Supports single Data object or list of Data objects
    - Handles nested dictionaries and extracts text from various locations
    - Uses safe string formatting with fallback for missing keys
    - Preserves original Data objects in output

    Args:
        template: Format string with placeholders (e.g., "Hello {text}")
                 Placeholders are replaced with values from Data objects
        data: Either a single Data object or a list of Data objects to format
              Each object can contain text, dictionaries, or nested data

    Returns:
        A tuple containing:
        - List[str]: Formatted strings based on the template
        - List[Data]: Original Data objects in the same order

    Raises:
        ValueError: If template is None
        TypeError: If template is not a string

    Examples:
        >>> result = data_to_text_list("Hello {text}", Data(text="world"))
        >>> assert result == (["Hello world"], [Data(text="world")])

        >>> result = data_to_text_list(
        ...     "{name} is {age}",
        ...     Data(data={"name": "Alice", "age": 25})
        ... )
        >>> assert result == (["Alice is 25"], [Data(data={"name": "Alice", "age": 25})])
    """
    # 输入为空时直接返回空列表
    if data is None:
        return [], []

    # 模板不能为 None
    if template is None:
        msg = "Template must be a string, but got None."
        raise ValueError(msg)

    # 模板必须是字符串类型
    if not isinstance(template, str):
        msg = f"Template must be a string, but got {type(template)}"
        raise TypeError(msg)

    # 格式化后的文本列表
    formatted_text: list[str] = []
    # 处理后的数据对象列表（保持与格式化文本一一对应）
    processed_data: list[Data] = []

    # 如果传入的是单个 Data 对象，转换为列表统一处理
    data_list = [data] if isinstance(data, Data) else data

    # 确保列表中每个元素都是 Data 对象，非 Data 类型用其字符串表示包装
    data_objects = [item if isinstance(item, Data) else Data(text=str(item)) for item in data_list]

    for data_obj in data_objects:
        # 构建模板替换字典
        format_dict = {}

        # 如果 data_obj.data 是字典，将其键值对展开到替换字典中
        if isinstance(data_obj.data, dict):
            format_dict.update(data_obj.data)

            # 处理嵌套的 "data" 字典，将其中的键值对也展开到替换字典
            if isinstance(data_obj.data.get("data"), dict):
                format_dict.update(data_obj.data["data"])

            # 如果存在错误信息，将错误信息也放入 "text" 键中
            elif format_dict.get("error"):
                format_dict["text"] = format_dict["error"]

        # 保留原始 data 对象引用，允许模板中通过 {data} 访问
        format_dict["data"] = data_obj.data

        # 使用 defaultdict 包装，未匹配的占位符将显示空字符串而非抛出 KeyError
        safe_dict = defaultdict(str, format_dict)

        try:
            # 执行模板格式化并收集结果
            formatted_text.append(template.format_map(safe_dict))
            processed_data.append(data_obj)
        except ValueError as e:
            msg = f"Error formatting template: {e!s}"
            raise ValueError(msg) from e

    return formatted_text, processed_data


def data_to_text(template: str, data: Data | list[Data], sep: str = "\n") -> str:
    r"""Converts data into a formatted text string based on a given template.

    根据模板将 Data 对象格式化为单个文本字符串。

    Args:
        template (str): The template string used to format each data item.
            用于格式化每个数据项的模板字符串。
        data (Data | list[Data]): A single data item or a list of data items to be formatted.
            要格式化的单个数据项或数据项列表。
        sep (str, optional): The separator to use between formatted data items. Defaults to "\n".
            格式化数据项之间的分隔符，默认为换行符。

    Returns:
        str: A string containing the formatted data items separated by the specified separator.
            包含格式化后数据项的字符串，各数据项之间用指定分隔符连接。
    """
    # 调用 data_to_text_list 获取格式化文本列表，忽略原始数据对象
    formatted_text, _ = data_to_text_list(template, data)
    # 分隔符为 None 时使用默认换行符
    sep = "\n" if sep is None else sep
    return sep.join(formatted_text)


def messages_to_text(template: str, messages: Message | list[Message]) -> str:
    """Converts a list of Messages to a list of texts.

    将消息列表转换为格式化文本字符串。

    Args:
        template (str): The template to use for the conversion.
            用于转换的模板字符串。
        messages (list[Message]): The list of Messages to convert.
            要转换的消息列表。

    Returns:
        list[str]: The converted list of texts.
            转换后的文本字符串。
    """
    # 将单个 Message 对象包装为列表，统一处理
    if isinstance(messages, (Message)):
        messages = [messages]
    # Check if there are any format strings in the template
    # 检查列表中所有元素是否都是 Message 类型
    messages_ = []
    for message in messages:
        # If it is not a message, create one with the key "text"
        # 验证消息类型，非 Message 类型则抛出异常
        if not isinstance(message, Message):
            msg = "All elements in the list must be of type Message."
            raise TypeError(msg)
        messages_.append(message)

    # 将每条消息序列化后填充到模板中，支持 {data} 和 **message 两种方式访问消息字段
    formated_messages = [template.format(data=message.model_dump(), **message.model_dump()) for message in messages_]
    return "\n".join(formated_messages)


def clean_string(s):
    """清理字符串中的空行和多余的连续换行符。

    Remove empty lines and normalize multiple consecutive newlines.
    """
    # Remove empty lines
    # 移除所有空行（仅包含空白字符的行）
    s = re.sub(r"^\s*$", "", s, flags=re.MULTILINE)
    # Replace three or more newlines with a double newline
    # 将三个及以上连续换行符替换为双换行符
    return re.sub(r"\n{3,}", "\n\n", s)


def _serialize_data(data: Data) -> str:
    """Serialize Data object to JSON string.

    将 Data 对象序列化为 JSON 字符串。
    """
    # Convert data.data to JSON-serializable format
    # 将 data.data 转换为 JSON 可序列化的格式
    serializable_data = jsonable_encoder(data.data)
    # Serialize with orjson, enabling pretty printing with indentation
    # 使用 orjson 序列化，开启缩进美化输出
    json_bytes = orjson.dumps(serializable_data, option=orjson.OPT_INDENT_2)
    # Convert bytes to string and wrap in Markdown code blocks
    # 将字节转换为字符串，并用 Markdown 代码块包裹
    return "```json\n" + json_bytes.decode("utf-8") + "\n```"


def safe_convert(data: Any, *, clean_data: bool = False) -> str:
    """Safely convert input data to string.

    安全地将输入数据转换为字符串，支持多种数据类型。
    """
    try:
        # 字符串类型直接清理后返回
        if isinstance(data, str):
            return clean_string(data)
        # Message 类型提取文本内容后返回
        if isinstance(data, Message):
            return data.get_text()
        # Data 类型序列化为 JSON 代码块后清理返回
        if isinstance(data, Data):
            return clean_string(_serialize_data(data))
        # DataFrame 类型转换为 Markdown 表格格式
        if isinstance(data, DataFrame):
            if clean_data:
                # Remove empty rows
                # 移除全为空值的行
                data = data.dropna(how="all")
                # Remove empty lines in each cell
                # 移除每个单元格中的空行
                data = data.replace(r"^\s*$", "", regex=True)
                # Replace multiple newlines with a single newline
                # 将多个连续换行符替换为单个换行符
                data = data.replace(r"\n+", "\n", regex=True)

            # Replace pipe characters to avoid markdown table issues
            # 转义管道符，避免破坏 Markdown 表格格式
            processed_data = data.replace(r"\|", r"\\|", regex=True)

            # 转换为 Markdown 表格格式（不包含行索引）
            return processed_data.to_markdown(index=False)

        # 其他类型统一转为字符串后清理
        return clean_string(str(data))
    except (ValueError, TypeError, AttributeError) as e:
        msg = f"Error converting data: {e!s}"
        raise ValueError(msg) from e


def data_to_dataframe(data: Data | list[Data]) -> DataFrame:
    """Converts a Data object or a list of Data objects to a DataFrame.

    将 Data 对象或 Data 对象列表转换为 DataFrame。

    Args:
        data (Data | list[Data]): The Data object or list of Data objects to convert.
            要转换的 Data 对象或 Data 对象列表。

    Returns:
        DataFrame: The converted DataFrame.
            转换后的 DataFrame。
    """
    # 单个 Data 对象直接包装为列表处理
    if isinstance(data, Data):
        return DataFrame([data.data])
    # 列表形式则提取每个 Data 对象的 data 属性
    return DataFrame(data=[d.data for d in data])
