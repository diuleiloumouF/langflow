# URL 解析模块，用于验证 Base URL 格式
from urllib.parse import urlparse

# PDF 读取器，用于验证高分辨率模式下上传的文件是否为有效 PDF
from pypdf import PdfReader

# 文件组件基类，提供文件处理的基础功能
from lfx.base.data.base_file import BaseFileComponent

# 各类输入组件，用于定义组件的用户界面参数
from lfx.inputs.inputs import BoolInput, DropdownInput, FloatInput, IntInput, MessageTextInput, SecretStrInput

# 数据模型，用于封装提取结果
from lfx.schema.data import Data


# NVIDIA NeMo 多模态文档提取组件
# 支持从 PDF、DOCX、PPTX、图片等多种格式中提取文本、表格、图表和图片
class NvidiaIngestComponent(BaseFileComponent):
    # 组件显示名称
    display_name = "NVIDIA Retriever Extraction"
    # 组件描述：使用 NVIDIA NeMo API 从文档中进行多模态数据提取
    description = "Multi-modal data extraction from documents using NVIDIA's NeMo API."
    # 文档链接
    documentation: str = "https://docs.nvidia.com/nemo/retriever/extraction/overview/"
    # 组件图标
    icon = "NVIDIA"
    # 标记为 Beta 功能
    beta = True

    try:
        from nv_ingest_client.util.file_processing.extract import EXTENSION_TO_DOCUMENT_TYPE

        # 支持的文件扩展名，来源：https://github.com/NVIDIA/nv-ingest/blob/main/README.md
        # 包括：PDF、Word、PowerPoint、JPEG、PNG、SVG、TIFF、TXT
        VALID_EXTENSIONS = ["pdf", "docx", "pptx", "jpeg", "png", "svg", "tiff", "txt"]
    except ImportError:
        # nv-ingest 为可选依赖，未安装时提示用户安装方式
        msg = (
            "NVIDIA Retriever Extraction (nv-ingest) is an optional dependency. "
            "Install with `uv pip install 'langflow[nv-ingest]'` "
            "(requires Python 3.12>=)"
        )
        VALID_EXTENSIONS = [msg]

    # 组件输入参数定义
    inputs = [
        # 继承基础文件组件的通用输入参数（如 file_path 等）
        *BaseFileComponent.get_base_inputs(),
        # --- API 连接配置 ---
        # NVIDIA NeMo API 的基础 URL 地址
        MessageTextInput(
            name="base_url",
            display_name="Base URL",
            info="The URL of the NVIDIA NeMo Retriever Extraction API.",
            required=True,
        ),
        # NVIDIA API 密钥，用于身份认证
        SecretStrInput(
            name="api_key",
            display_name="NVIDIA API Key",
        ),
        # --- 提取内容类型配置 ---
        # 是否从文档中提取文本
        BoolInput(
            name="extract_text",
            display_name="Extract Text",
            info="Extract text from documents",
            value=True,
        ),
        # 是否从图表中提取文本
        BoolInput(
            name="extract_charts",
            display_name="Extract Charts",
            info="Extract text from charts",
            value=False,
        ),
        # 是否从表格中提取文本
        BoolInput(
            name="extract_tables",
            display_name="Extract Tables",
            info="Extract text from tables",
            value=False,
        ),
        # 是否从文档中提取图片
        BoolInput(
            name="extract_images",
            display_name="Extract Images",
            info="Extract images from document",
            value=True,
        ),
        # 是否从文档中提取信息图
        BoolInput(
            name="extract_infographics",
            display_name="Extract Infographics",
            info="Extract infographics from document",
            value=False,
            advanced=True,
        ),
        # --- 文本提取深度配置 ---
        # 文本提取的粒度级别（在分块之前生效），不同文档类型对 block/line/span 的支持程度不同
        DropdownInput(
            name="text_depth",
            display_name="Text Depth",
            info=(
                "Level at which text is extracted (applies before splitting). "
                "Support for 'block', 'line', 'span' varies by document type."
            ),
            options=["document", "page", "block", "line", "span"],
            value="page",  # Default value
            advanced=True,
        ),
        # --- 文本分块配置 ---
        # 是否将提取的文本分割为更小的块
        BoolInput(
            name="split_text",
            display_name="Split Text",
            info="Split text into smaller chunks",
            value=True,
            advanced=True,
        ),
        # 每个文本块的最大 token 数量
        IntInput(
            name="chunk_size",
            display_name="Chunk size",
            info="The number of tokens per chunk",
            value=500,
            advanced=True,
        ),
        # 相邻文本块之间的重叠 token 数量
        IntInput(
            name="chunk_overlap",
            display_name="Chunk Overlap",
            info="Number of tokens to overlap from previous chunk",
            value=150,
            advanced=True,
        ),
        # --- 图片过滤配置 ---
        # 是否启用图片过滤功能
        BoolInput(
            name="filter_images",
            display_name="Filter Images",
            info="Filter images (see advanced options for filtering criteria).",
            advanced=True,
            value=False,
        ),
        # 图片最小尺寸过滤（单位：像素）
        IntInput(
            name="min_image_size",
            display_name="Minimum Image Size Filter",
            info="Minimum image width/length in pixels",
            value=128,
            advanced=True,
        ),
        # 最小宽高比（width / height），低于此值的图片将被过滤
        FloatInput(
            name="min_aspect_ratio",
            display_name="Minimum Aspect Ratio Filter",
            info="Minimum allowed aspect ratio (width / height). Images narrower than this will be filtered out.",
            value=0.2,
            advanced=True,
        ),
        # 最大宽高比（width / height），高于此值的图片将被过滤
        FloatInput(
            name="max_aspect_ratio",
            display_name="Maximum Aspect Ratio Filter",
            info="Maximum allowed aspect ratio (width / height). Images taller than this will be filtered out.",
            value=5.0,
            advanced=True,
        ),
        # 是否去除重复图片
        BoolInput(
            name="dedup_images",
            display_name="Deduplicate Images",
            info="Filter duplicated images.",
            advanced=True,
            value=True,
        ),
        # 是否使用 NVIDIA 模型为图片生成描述文字
        BoolInput(
            name="caption_images",
            display_name="Caption Images",
            info="Generate captions for images using the NVIDIA captioning model.",
            advanced=True,
            value=True,
        ),
        # 高分辨率模式（仅支持 PDF），可提升扫描件 PDF 的提取质量
        BoolInput(
            name="high_resolution",
            display_name="High Resolution (PDF only)",
            info=("Process pdf in high-resolution mode for better quality extraction from scanned pdf."),
            advanced=True,
            value=False,
        ),
    ]

    # 组件输出：继承基础文件组件的输出定义
    outputs = [
        *BaseFileComponent.get_base_outputs(),
    ]

    # 处理文件列表：调用 NVIDIA NeMo API 进行多模态数据提取
    def process_files(self, file_list: list[BaseFileComponent.BaseFile]) -> list[BaseFileComponent.BaseFile]:
        try:
            from nv_ingest_client.client import Ingestor
        except ImportError as e:
            # nv-ingest 客户端依赖未安装，提示用户安装
            msg = (
                "NVIDIA Retriever Extraction (nv-ingest) dependencies missing. "
                "Please install them using your package manager. (e.g. uv pip install langflow[nv-ingest])"
            )
            raise ImportError(msg) from e

        if not file_list:
            # 文件列表为空，抛出异常
            err_msg = "No files to process."
            self.log(err_msg)
            raise ValueError(err_msg)

        # 高分辨率模式下验证所有文件是否为有效的 PDF
        if self.high_resolution:
            for file in file_list:
                try:
                    with file.path.open("rb") as f:
                        PdfReader(f)
                except Exception as exc:
                    error_msg = "High-resolution mode only supports valid PDF files."
                    self.log(error_msg)
                    raise ValueError(error_msg) from exc

        # 获取所有文件的路径列表
        file_paths = [str(file.path) for file in file_list]

        # 验证 Base URL 格式
        self.base_url: str | None = self.base_url.strip() if self.base_url else None
        if self.base_url:
            try:
                urlparse(self.base_url)
            except Exception as e:
                error_msg = f"Invalid Base URL format: {e}"
                self.log(error_msg)
                raise ValueError(error_msg) from e
        else:
            # Base URL 为必填项
            base_url_error = "Base URL is required"
            raise ValueError(base_url_error)

        self.log(
            f"Creating Ingestor for Base URL: {self.base_url!r}",
        )

        try:
            # 创建 Ingestor 实例并配置提取参数
            ingestor = (
                Ingestor(
                    message_client_kwargs={
                        "base_url": self.base_url,
                        "headers": {"Authorization": f"Bearer {self.api_key}"},
                        "max_retries": 3,
                        "timeout": 60,
                    }
                )
                .files(file_paths)
                .extract(
                    extract_text=self.extract_text,
                    extract_tables=self.extract_tables,
                    extract_charts=self.extract_charts,
                    extract_images=self.extract_images,
                    extract_infographics=self.extract_infographics,
                    text_depth=self.text_depth,
                    # 高分辨率模式使用 nemoretriever_parse 提取方法
                    **({"extract_method": "nemoretriever_parse"} if self.high_resolution else {}),
                )
            )

            # 图片后处理：去重、过滤、生成描述
            if self.extract_images:
                if self.dedup_images:
                    ingestor = ingestor.dedup(content_type="image", filter=True)

                if self.filter_images:
                    ingestor = ingestor.filter(
                        content_type="image",
                        min_size=self.min_image_size,
                        min_aspect_ratio=self.min_aspect_ratio,
                        max_aspect_ratio=self.max_aspect_ratio,
                        filter=True,
                    )

                if self.caption_images:
                    ingestor = ingestor.caption()

            # 文本分块处理：使用 e5-large-unsupervised 分词器
            if self.extract_text and self.split_text:
                ingestor = ingestor.split(
                    tokenizer="intfloat/e5-large-unsupervised",
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    params={"split_source_types": ["PDF"]},
                )

            # 执行数据提取
            result = ingestor.ingest()
        except Exception as e:
            ingest_error = f"Error during ingestion: {e}"
            self.log(ingest_error)
            raise

        self.log(f"Results: {result}")

        # 存储提取结果的列表，每个元素为 Data 对象或 None
        data: list[Data | None] = []
        # 文档类型常量
        document_type_text = "text"
        document_type_structured = "structured"

        # 遍历提取结果：结果是按 text_depth 选项划分的分段列表
        # 如果 text_depth 为 "document"，则只有一个分段；每个分段包含多个元素（文本、结构化数据、图片）
        for segment in result:
            if segment:
                for element in segment:
                    document_type = element.get("document_type")
                    metadata = element.get("metadata", {})
                    source_metadata = metadata.get("source_metadata", {})

                    # 文本类型：直接提取内容
                    if document_type == document_type_text:
                        data.append(
                            Data(
                                text=metadata.get("content", ""),
                                file_path=source_metadata.get("source_name", ""),
                                document_type=document_type,
                                metadata=metadata,
                            )
                        )
                    # 结构化数据类型（图表和表格都返回为此类型）
                    # 提取的文本存储在 "table_content" 字段中
                    elif document_type == document_type_structured:
                        table_metadata = metadata.get("table_metadata", {})

                        # 将图表/表格的图片内容转换为二进制数据格式
                        if "content" in metadata:
                            metadata["content"] = {"$binary": metadata["content"]}

                        data.append(
                            Data(
                                text=table_metadata.get("table_content", ""),
                                file_path=source_metadata.get("source_name", ""),
                                document_type=document_type,
                                metadata=metadata,
                            )
                        )
                    # 图片类型：提取图片元数据和描述文字
                    elif document_type == "image":
                        image_metadata = metadata.get("image_metadata", {})

                        # 将图片内容转换为二进制数据格式
                        if "content" in metadata:
                            metadata["content"] = {"$binary": metadata["content"]}

                        data.append(
                            Data(
                                # 如果没有生成描述，则使用默认文本
                                text=image_metadata.get("caption", "No caption available"),
                                file_path=source_metadata.get("source_name", ""),
                                document_type=document_type,
                                metadata=metadata,
                            )
                        )
                    else:
                        # 不支持的文档类型，记录日志
                        self.log(f"Unsupported document type {document_type}")
        self.status = data or "No data"

        # 将提取的数据与原始 BaseFile 对象合并后返回
        return self.rollup_data(file_list, data)
