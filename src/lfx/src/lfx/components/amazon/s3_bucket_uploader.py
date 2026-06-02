from pathlib import Path
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import (
    BoolInput,
    DropdownInput,
    HandleInput,
    Output,
    SecretStrInput,
    StrInput,
)


class S3BucketUploaderComponent(Component):
    """S3BucketUploaderComponent is a component responsible for uploading files to an S3 bucket.

    It provides two strategies for file upload: "By Data" and "By File Name". The component
    requires AWS credentials and bucket details as inputs and processes files accordingly.

    Attributes:
        display_name (str): The display name of the component.
        description (str): A brief description of the components functionality.
        icon (str): The icon representing the component.
        name (str): The internal name of the component.
        inputs (list): A list of input configurations required by the component.
        outputs (list): A list of output configurations provided by the component.

    Methods:
        process_files() -> None:
            Processes files based on the selected strategy. Calls the appropriate method
            based on the strategy attribute.
        process_files_by_data() -> None:
            Processes and uploads files to an S3 bucket based on the data inputs. Iterates
            over the data inputs, logs the file path and text content, and uploads each file
            to the specified S3 bucket if both file path and text content are available.
        process_files_by_name() -> None:
            Processes and uploads files to an S3 bucket based on their names. Iterates through
            the list of data inputs, retrieves the file path from each data item, and uploads
            the file to the specified S3 bucket if the file path is available. Logs the file
            path being uploaded.
        _s3_client() -> Any:
            Creates and returns an S3 client using the provided AWS access key ID and secret
            access key.

        Please note that this component requires the boto3 library to be installed. It is designed
        to work with File and Director components as inputs
    """

    # 组件显示名称
    display_name = "S3 Bucket Uploader"
    # 组件功能简述：上传文件到 S3 存储桶
    description = "Uploads files to S3 bucket."
    # 组件图标，使用 Amazon 图标
    icon = "Amazon"
    # 组件内部标识名称
    name = "s3bucketuploader"

    # 组件输入参数定义
    inputs = [
        # AWS 访问密钥 ID，密码类型输入，必填
        SecretStrInput(
            name="aws_access_key_id",
            display_name="AWS Access Key ID",
            required=True,
            password=True,
            info="AWS Access key ID.",
        ),
        # AWS 密钥，密码类型输入，必填
        SecretStrInput(
            name="aws_secret_access_key",
            display_name="AWS Secret Key",
            required=True,
            password=True,
            info="AWS Secret Key.",
        ),
        # S3 存储桶名称
        StrInput(
            name="bucket_name",
            display_name="Bucket Name",
            info="Enter the name of the bucket.",
            advanced=False,
        ),
        # 文件上传策略选择：按数据内容存储或按原始文件存储
        DropdownInput(
            name="strategy",
            display_name="Strategy for file upload",
            options=["Store Data", "Store Original File"],
            value="By Data",
            info=(
                "Choose the strategy to upload the file. By Data means that the source file "
                "is parsed and stored as LangFlow data. By File Name means that the source "
                "file is uploaded as is."
            ),
        ),
        # 数据输入句柄，接收来自上游组件的 Data 或 JSON 数据
        HandleInput(
            name="data_inputs",
            display_name="Data Inputs",
            info="The data to split.",
            input_types=["Data", "JSON"],
            is_list=True,
            required=True,
        ),
        # S3 对象键前缀，用于组织上传的文件
        StrInput(
            name="s3_prefix",
            display_name="S3 Prefix",
            info="Prefix for all files.",
            advanced=True,
        ),
        # 是否去除文件路径中的目录部分，只保留文件名
        BoolInput(
            name="strip_path",
            display_name="Strip Path",
            info="Removes path from file path.",
            required=True,
            advanced=True,
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(display_name="Writes to AWS Bucket", name="data", method="process_files"),
    ]

    def process_files(self) -> None:
        """Process files based on the selected strategy.

        This method uses a strategy pattern to process files. The strategy is determined
        by the `self.strategy` attribute, which can be either "By Data" or "By File Name".
        Depending on the strategy, the corresponding method (`process_files_by_data` or
        process_files_by_name`) is called. If an invalid strategy is provided, an error
        is logged.

        Returns:
            None
        """
        # 策略模式：根据用户选择的策略调用对应的处理方法
        strategy_methods = {
            # 按数据内容存储
            "Store Data": self.process_files_by_data,
            # 按原始文件存储
            "Store Original File": self.process_files_by_name,
        }
        # 获取对应策略的方法并执行，如果策略无效则记录日志
        strategy_methods.get(self.strategy, lambda: self.log("Invalid strategy"))()

    def process_files_by_data(self) -> None:
        """Processes and uploads files to an S3 bucket based on the data inputs.

        This method iterates over the data inputs, logs the file path and text content,
        and uploads each file to the specified S3 bucket if both file path and text content
        are available.

        Args:
            None

        Returns:
            None
        """
        # 遍历所有输入数据项，将文本内容作为对象体上传到 S3
        for data_item in self.data_inputs:
            file_path = data_item.data.get("file_path")
            text_content = data_item.data.get("text")

            # 仅当文件路径和文本内容都存在时才上传
            if file_path and text_content:
                self._s3_client().put_object(
                    Bucket=self.bucket_name, Key=self._normalize_path(file_path), Body=text_content
                )

    def process_files_by_name(self) -> None:
        """Processes and uploads files to an S3 bucket based on their names.

        Iterates through the list of data inputs, retrieves the file path from each data item,
        and uploads the file to the specified S3 bucket if the file path is available.
        Logs the file path being uploaded.

        Returns:
            None
        """
        # 遍历所有输入数据项，将原始文件直接上传到 S3
        for data_item in self.data_inputs:
            file_path = data_item.data.get("file_path")
            self.log(f"Uploading file: {file_path}")
            # 仅当文件路径存在时才上传
            if file_path:
                self._s3_client().upload_file(file_path, Bucket=self.bucket_name, Key=self._normalize_path(file_path))

    def _s3_client(self) -> Any:
        """Creates and returns an S3 client using the provided AWS access key ID and secret access key.

        Returns:
            Any: A boto3 S3 client instance.
        """
        # 延迟导入 boto3，仅在需要时检查是否安装
        try:
            import boto3
        except ImportError as e:
            msg = "boto3 is not installed. Please install it using `uv pip install boto3`."
            raise ImportError(msg) from e

        # 使用 AWS 凭证创建并返回 S3 客户端
        return boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

    def _normalize_path(self, file_path) -> str:
        """Process the file path based on the s3_prefix and path_as_prefix.

        Args:
            file_path (str): The original file path.
            s3_prefix (str): The S3 prefix to use.
            path_as_prefix (bool): Whether to use the file path as the S3 prefix.

        Returns:
            str: The processed file path.
        """
        # 获取配置的 S3 前缀
        prefix = self.s3_prefix
        # 获取是否去除路径的配置
        strip_path = self.strip_path
        processed_path: str = file_path

        if strip_path:
            # Filename only
            # 仅保留文件名，去除目录路径
            processed_path = Path(file_path).name

        # Concatenate the s3_prefix if it exists
        # 如果配置了 S3 前缀，则拼接到路径前面
        if prefix:
            processed_path = str(Path(prefix) / processed_path)

        return processed_path
