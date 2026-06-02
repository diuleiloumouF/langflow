import csv
import io
from pathlib import Path

from lfx.base.data.storage_utils import read_file_text
from lfx.custom.custom_component.component import Component
from lfx.io import FileInput, MessageTextInput, MultilineInput, Output
from lfx.schema.data import Data
from lfx.utils.async_helpers import run_until_complete


class CSVToDataComponent(Component):
    # CSV 转 Data 组件：支持从文件上传、文件路径或 CSV 字符串加载 CSV 数据，转换为 Data 对象列表
    # 该组件已标记为 legacy，推荐使用 data.File 替代
    display_name = "Load CSV"
    description = "Load a CSV file, CSV from a file path, or a valid CSV string and convert it to a list of Data"
    icon = "file-spreadsheet"
    name = "CSVtoData"
    legacy = True
    replacement = ["data.File"]

    # 组件输入参数定义
    inputs = [
        FileInput(
            name="csv_file",
            display_name="CSV File",
            file_types=["csv"],
            info="Upload a CSV file to convert to a list of Data objects",
        ),
        MessageTextInput(
            name="csv_path",
            display_name="CSV File Path",
            info="Provide the path to the CSV file as pure text",
        ),
        MultilineInput(
            name="csv_string",
            display_name="CSV String",
            info="Paste a CSV string directly to convert to a list of Data objects",
        ),
        MessageTextInput(
            name="text_key",
            display_name="Text Key",
            info="The key to use for the text column. Defaults to 'text'.",
            value="text",
        ),
    ]

    # 组件输出定义：将 CSV 转换为 Data 列表
    outputs = [
        Output(name="data_list", display_name="JSON List", method="load_csv_to_data"),
    ]

    # 将 CSV 数据加载并转换为 Data 对象列表
    # 支持三种输入方式：CSV 文件上传、文件路径、CSV 字符串
    # 三种输入方式互斥，只能选择其中一种
    def load_csv_to_data(self) -> list[Data]:
        # 验证输入：必须且只能提供一种 CSV 输入方式
        if sum(bool(field) for field in [self.csv_file, self.csv_path, self.csv_string]) != 1:
            msg = "Please provide exactly one of: CSV file, file path, or CSV string."
            raise ValueError(msg)

        csv_data = None
        try:
            # 处理 CSV 文件上传
            if self.csv_file:
                # FileInput always provides a local file path
                file_path = self.csv_file
                if not file_path.lower().endswith(".csv"):
                    self.status = "The provided file must be a CSV file."
                else:
                    # Resolve to absolute path and read from local filesystem
                    resolved_path = self.resolve_path(file_path)
                    csv_bytes = Path(resolved_path).read_bytes()
                    csv_data = csv_bytes.decode("utf-8")

            # 处理 CSV 文件路径
            elif self.csv_path:
                file_path = self.csv_path
                if not file_path.lower().endswith(".csv"):
                    self.status = "The provided path must be to a CSV file."
                else:
                    csv_data = run_until_complete(
                        read_file_text(file_path, encoding="utf-8", resolve_path=self.resolve_path, newline="")
                    )

            # 处理 CSV 字符串输入
            else:
                csv_data = self.csv_string

            # 解析 CSV 数据并转换为 Data 对象列表
            if csv_data:
                csv_reader = csv.DictReader(io.StringIO(csv_data))
                result = [Data(data=row, text_key=self.text_key) for row in csv_reader]

                if not result:
                    self.status = "The CSV data is empty."
                    return []

                self.status = result
                return result

        # CSV 解析错误处理
        except csv.Error as e:
            error_message = f"CSV parsing error: {e}"
            self.status = error_message
            raise ValueError(error_message) from e

        # 其他异常处理
        except Exception as e:
            error_message = f"An error occurred: {e}"
            self.status = error_message
            raise ValueError(error_message) from e

        # An error occurred
        raise ValueError(self.status)
