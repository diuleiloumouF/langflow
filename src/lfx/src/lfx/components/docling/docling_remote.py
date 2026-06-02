# Base64 编码
import base64

# 时间处理
import time

# 并发执行
from concurrent.futures import Future, ThreadPoolExecutor

# 路径处理
from pathlib import Path

# 类型注解
from typing import Any

# HTTP 客户端库
import httpx

# Docling 文档类型
from docling_core.types.doc import DoclingDocument

# Pydantic 验证错误
from pydantic import ValidationError

# 文件组件基类
from lfx.base.data import BaseFileComponent

# 输入组件类型
from lfx.inputs import IntInput, NestedDictInput, StrInput
from lfx.inputs.inputs import FloatInput

# 数据模型
from lfx.schema import Data

# URL 转换工具（将 localhost 转换为容器可访问的地址）
from lfx.utils.util import transform_localhost_url


# Docling 远程组件，通过连接 Docling Serve 实例处理输入文档
class DoclingRemoteComponent(BaseFileComponent):
    display_name = "Docling Serve"
    description = "Uses Docling to process input documents connecting to your instance of Docling Serve."
    documentation = "https://docling-project.github.io/docling/"
    trace_type = "tool"
    icon = "Docling"
    name = "DoclingRemote"

    # HTTP 5xx 错误的最大重试次数
    MAX_500_RETRIES = 5

    # 支持的文件扩展名列表
    # https://docling-project.github.io/docling/usage/supported_formats/
    VALID_EXTENSIONS = [
        "adoc",
        "asciidoc",
        "asc",
        "bmp",
        "csv",
        "dotx",
        "dotm",
        "docm",
        "docx",
        "htm",
        "html",
        "jpeg",
        "jpg",
        "json",
        "md",
        "pdf",
        "png",
        "potx",
        "ppsx",
        "pptm",
        "potm",
        "ppsm",
        "pptx",
        "tiff",
        "txt",
        "xls",
        "xlsx",
        "xhtml",
        "xml",
        "webp",
    ]

    # 输入参数定义
    inputs = [
        # 继承父类的基础输入参数
        *BaseFileComponent.get_base_inputs(),
        # Docling Serve 服务器地址
        StrInput(
            name="api_url",
            display_name="Server address",
            info="URL of the Docling Serve instance.",
            required=True,
        ),
        # 最大并发请求数
        IntInput(
            name="max_concurrency",
            display_name="Concurrency",
            info="Maximum number of concurrent requests for the server.",
            advanced=True,
            value=2,
            input_types=["Message"],
        ),
        # 最大轮询等待时间（秒）
        FloatInput(
            name="max_poll_timeout",
            display_name="Maximum poll time",
            info="Maximum waiting time for the document conversion to complete.",
            advanced=True,
            value=3600,
            input_types=["Message"],
        ),
        # 额外的 HTTP 请求头
        NestedDictInput(
            name="api_headers",
            display_name="HTTP headers",
            advanced=True,
            required=False,
            info=("Optional dictionary of additional headers required for connecting to Docling Serve."),
            input_types=["Message"],
        ),
        # Docling Serve 的额外选项
        NestedDictInput(
            name="docling_serve_opts",
            display_name="Docling options",
            advanced=True,
            required=False,
            info=(
                "Optional dictionary of additional options. "
                "See https://github.com/docling-project/docling-serve/blob/main/docs/usage.md for more information."
            ),
            input_types=["Message"],
        ),
    ]

    # 输出参数定义
    outputs = [
        *BaseFileComponent.get_base_outputs(),
    ]

    # 处理文件列表：将文件发送到 Docling Serve 进行转换
    def process_files(self, file_list: list[BaseFileComponent.BaseFile]) -> list[BaseFileComponent.BaseFile]:
        # 在容器环境中运行时，将 localhost URL 转换为容器可访问的地址
        transformed_url = transform_localhost_url(self.api_url)
        base_url = f"{transformed_url}/v1"

        # 内部函数：将单个文档转换为 Docling 格式
        def _convert_document(client: httpx.Client, file_path: Path, options: dict[str, Any]) -> Data | None:
            # 将文件内容编码为 Base64
            encoded_doc = base64.b64encode(file_path.read_bytes()).decode()
            payload = {
                "options": options,
                "sources": [{"kind": "file", "base64_string": encoded_doc, "filename": file_path.name}],
            }

            # 提交异步转换任务
            response = client.post(f"{base_url}/convert/source/async", json=payload)
            response.raise_for_status()
            task = response.json()

            # 轮询任务状态
            http_failures = 0
            retry_status_start = 500
            retry_status_end = 600
            start_wait_time = time.monotonic()
            while task["task_status"] not in ("success", "failure"):
                # 检查是否超过最大轮询超时时间
                processing_time = time.monotonic() - start_wait_time
                if processing_time >= self.max_poll_timeout:
                    msg = (
                        f"Processing time {processing_time=} exceeds the maximum poll timeout {self.max_poll_timeout=}."
                        "Please increase the max_poll_timeout parameter or review why the processing "
                        "takes long on the server."
                    )
                    self.log(msg)
                    raise RuntimeError(msg)

                # 等待后查询新状态
                time.sleep(2)
                response = client.get(f"{base_url}/status/poll/{task['task_id']}")

                # 检查状态请求是否遇到 5xx 错误并重试
                if retry_status_start <= response.status_code < retry_status_end:
                    http_failures += 1
                    if http_failures > self.MAX_500_RETRIES:
                        self.log(f"The status requests got a http response {response.status_code} too many times.")
                        return None
                    continue

                # 更新任务状态
                task = response.json()

            # 获取转换结果
            result_resp = client.get(f"{base_url}/result/{task['task_id']}")
            result_resp.raise_for_status()
            result = result_resp.json()

            # 检查结果中是否包含 JSON DoclingDocument
            if "json_content" not in result["document"] or result["document"]["json_content"] is None:
                self.log("No JSON DoclingDocument found in the result.")
                return None

            # 验证并构建 DoclingDocument 对象
            try:
                doc = DoclingDocument.model_validate(result["document"]["json_content"])
                return Data(data={"doc": doc, "file_path": str(file_path)})
            except ValidationError as e:
                self.log(f"Error validating the document. {e}")
                return None

        # 配置 Docling 选项
        docling_options = {
            "to_formats": ["json"],
            "image_export_mode": "placeholder",
            **(self.docling_serve_opts or {}),
        }

        # 使用线程池并发处理多个文件
        processed_data: list[Data | None] = []
        with (
            httpx.Client(headers=self.api_headers) as client,
            ThreadPoolExecutor(max_workers=self.max_concurrency) as executor,
        ):
            futures: list[tuple[int, Future]] = []
            for i, file in enumerate(file_list):
                if file.path is None:
                    processed_data.append(None)
                    continue

                # 提交文件转换任务到线程池
                futures.append((i, executor.submit(_convert_document, client, file.path, docling_options)))

            # 收集所有任务的结果
            for _index, future in futures:
                try:
                    result_data = future.result()
                    processed_data.append(result_data)
                except (httpx.HTTPStatusError, httpx.RequestError, KeyError, ValueError) as exc:
                    self.log(f"Docling remote processing failed: {exc}")
                    raise

        return self.rollup_data(file_list, processed_data)
