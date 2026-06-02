# 该文件定义了 JSONToDataComponent 组件，用于将 JSON 文件、文件路径或 JSON 字符串转换为 Data 对象
import json
from pathlib import Path

from json_repair import repair_json

from lfx.base.data.storage_utils import read_file_text
from lfx.custom.custom_component.component import Component
from lfx.io import FileInput, MessageTextInput, MultilineInput, Output
from lfx.schema.data import Data
from lfx.utils.async_helpers import run_until_complete


# JSON 转 Data 组件：支持三种输入方式（上传文件、文件路径、JSON 字符串），将 JSON 数据统一转换为 Data 对象
class JSONToDataComponent(Component):
    # 在画布上显示的组件名称
    display_name = "Load JSON"
    # 组件功能描述
    description = (
        "Convert a JSON file, JSON from a file path, or a JSON string to a Data object or a list of Data objects"
    )
    # 画布上的图标标识
    icon = "braces"
    # 组件内部唯一标识符，用于序列化和反序列化
    name = "JSONtoData"
    # 标记为遗留组件，不再维护，建议使用 replacement 指定的替代组件
    legacy = True
    # 推荐的替代组件，用户可迁移到 data.File
    replacement = ["data.File"]

    # 组件输入定义：三种输入方式，用户只能选择其中一种
    inputs = [
        # 输入方式一：直接上传 JSON 文件
        FileInput(
            name="json_file",
            display_name="JSON File",
            file_types=["json"],
            info="Upload a JSON file to convert to a Data object or list of Data objects",
        ),
        # 输入方式二：提供 JSON 文件的路径（本地路径或 S3 路径）
        MessageTextInput(
            name="json_path",
            display_name="JSON File Path",
            info="Provide the path to the JSON file as pure text",
        ),
        # 输入方式三：直接输入 JSON 字符串（对象或数组格式）
        MultilineInput(
            name="json_string",
            display_name="JSON String",
            info="Enter a valid JSON string (object or array) to convert to a Data object or list of Data objects",
        ),
    ]

    # 组件输出定义：将转换后的 Data 对象输出
    outputs = [
        Output(name="data", display_name="JSON", method="convert_json_to_data"),
    ]

    # 将 JSON 数据转换为 Data 对象或 Data 对象列表
    def convert_json_to_data(self) -> Data | list[Data]:
        # 校验：必须且只能提供一种输入方式
        if sum(bool(field) for field in [self.json_file, self.json_path, self.json_string]) != 1:
            msg = "Please provide exactly one of: JSON file, file path, or JSON string."
            self.status = msg
            raise ValueError(msg)

        json_data = None

        try:
            # 方式一：从上传的文件中读取 JSON 内容
            if self.json_file:
                # FileInput always provides a local file path
                file_path = self.json_file
                if not file_path.lower().endswith(".json"):
                    self.status = "The provided file must be a JSON file."
                else:
                    # Resolve to absolute path and read from local filesystem
                    resolved_path = self.resolve_path(file_path)
                    json_data = Path(resolved_path).read_text(encoding="utf-8")

            # 方式二：通过文件路径读取 JSON 内容
            elif self.json_path:
                # User-provided text path - could be local or S3 key
                file_path = self.json_path
                if not file_path.lower().endswith(".json"):
                    self.status = "The provided path must be to a JSON file."
                else:
                    json_data = run_until_complete(
                        read_file_text(file_path, encoding="utf-8", resolve_path=self.resolve_path)
                    )

            # 方式三：直接使用用户输入的 JSON 字符串
            else:
                json_data = self.json_string

            if json_data:
                # 尝试解析 JSON 字符串
                try:
                    parsed_data = json.loads(json_data)
                except json.JSONDecodeError:
                    # 解析失败时，使用 json_repair 库尝试修复格式错误的 JSON
                    repaired_json_string = repair_json(json_data)
                    parsed_data = json.loads(repaired_json_string)

                # 根据解析结果类型决定返回单个 Data 还是 Data 列表
                if isinstance(parsed_data, list):
                    # JSON 数组：每个元素转换为一个 Data 对象，返回列表
                    result = [Data(data=item) for item in parsed_data]
                else:
                    # JSON 对象：直接转换为单个 Data 对象
                    result = Data(data=parsed_data)
                self.status = result
                return result

        # 捕获 JSON 解析错误、语法错误和值错误
        except (json.JSONDecodeError, SyntaxError, ValueError) as e:
            error_message = f"Invalid JSON or Python literal: {e}"
            self.status = error_message
            raise ValueError(error_message) from e

        # 捕获其他未预期的异常
        except Exception as e:
            error_message = f"An error occurred: {e}"
            self.status = error_message
            raise ValueError(error_message) from e

        # 所有输入都为空时的兜底错误处理
        raise ValueError(self.status)
