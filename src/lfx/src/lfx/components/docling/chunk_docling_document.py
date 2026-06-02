# JSON 序列化
import json

# tiktoken 分词器（用于 OpenAI 模型）
import tiktoken

# Docling 文档分块器基类和元数据
from docling_core.transforms.chunker import BaseChunker, DocMeta

# Docling 层级分块器
from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker

# Docling 文档提取工具函数
from lfx.base.data.docling_utils import extract_docling_documents

# 组件基类
from lfx.custom import Component

# 输入组件类型
from lfx.io import BoolInput, DropdownInput, HandleInput, IntInput, MessageTextInput, Output, StrInput

# 数据模型
from lfx.schema import Data, DataFrame


# Docling 文档分块组件，用于将文档分割为更小的块
class ChunkDoclingDocumentComponent(Component):
    display_name: str = "Chunk DoclingDocument"
    description: str = "Use the DocumentDocument chunkers to split the document into chunks."
    documentation = "https://docling-project.github.io/docling/concepts/chunking/"
    icon = "Docling"
    name = "ChunkDoclingDocument"

    # 输入参数定义
    inputs = [
        # 输入数据：包含待分块的文档
        HandleInput(
            name="data_inputs",
            display_name="JSON or Table",
            info="The data with documents to split in chunks.",
            input_types=["Data", "JSON", "DataFrame", "Table"],
            required=True,
        ),
        # 分块器类型选择
        DropdownInput(
            name="chunker",
            display_name="Chunker",
            options=["HybridChunker", "HierarchicalChunker"],
            info=("Which chunker to use."),
            value="HybridChunker",
            real_time_refresh=True,
            input_types=["Message"],
        ),
        # 分词器提供者（仅 HybridChunker 可用）
        DropdownInput(
            name="provider",
            display_name="Provider",
            options=["Hugging Face", "OpenAI"],
            info=("Which tokenizer provider."),
            value="Hugging Face",
            show=True,
            real_time_refresh=True,
            advanced=True,
            dynamic=True,
        ),
        # Hugging Face 分词器模型名称
        StrInput(
            name="hf_model_name",
            display_name="HF model name",
            info=(
                "Model name of the tokenizer to use with the HybridChunker when Hugging Face is chosen as a tokenizer."
            ),
            value="sentence-transformers/all-MiniLM-L6-v2",
            show=True,
            advanced=True,
            dynamic=True,
        ),
        # OpenAI 分词器模型名称
        StrInput(
            name="openai_model_name",
            display_name="OpenAI model name",
            info=("Model name of the tokenizer to use with the HybridChunker when OpenAI is chosen as a tokenizer."),
            value="gpt-4o",
            show=False,
            advanced=True,
            dynamic=True,
        ),
        # HybridChunker 的最大 token 数量
        IntInput(
            name="max_tokens",
            display_name="Maximum tokens",
            info=("Maximum number of tokens for the HybridChunker."),
            show=True,
            required=False,
            advanced=True,
            dynamic=True,
            input_types=["Message"],
        ),
        # 是否合并共享相同元数据的小块
        BoolInput(
            name="merge_peers",
            display_name="Merge peers",
            info="Merge undersized chunks sharing the same relevant metadata.",
            value=True,
            show=True,
            advanced=True,
            dynamic=True,
        ),
        # 是否始终输出标题（即使为空节）
        BoolInput(
            name="always_emit_headings",
            display_name="Always emit headings",
            info="Emit headings even for empty sections.",
            value=False,
            show=True,
            advanced=True,
            dynamic=True,
        ),
        # DoclingDocument 列的键名
        MessageTextInput(
            name="doc_key",
            display_name="Doc Key",
            info="The key to use for the DoclingDocument column.",
            value="doc",
            advanced=True,
        ),
    ]

    # 输出参数定义：返回分块后的表格数据
    outputs = [
        Output(display_name="Table", name="dataframe", method="chunk_documents"),
    ]

    # 根据分块器和提供者选择动态更新构建配置
    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None) -> dict:
        """Update build_config to show/hide fields based on chunker and provider selection."""
        if field_name == "chunker":
            provider_type = build_config["provider"]["value"]
            is_hf = provider_type == "Hugging Face"
            is_openai = provider_type == "OpenAI"
            if field_value == "HybridChunker":
                # HybridChunker 模式：显示分词器相关配置
                build_config["provider"]["show"] = True
                build_config["hf_model_name"]["show"] = is_hf
                build_config["openai_model_name"]["show"] = is_openai
                build_config["max_tokens"]["show"] = True
                build_config["merge_peers"]["show"] = True
                build_config["always_emit_headings"]["show"] = True
            else:
                # HierarchicalChunker 模式：隐藏分词器相关配置
                build_config["provider"]["show"] = False
                build_config["hf_model_name"]["show"] = False
                build_config["openai_model_name"]["show"] = False
                build_config["max_tokens"]["show"] = False
                build_config["merge_peers"]["show"] = False
                build_config["always_emit_headings"]["show"] = False
        elif field_name == "provider" and build_config["chunker"]["value"] == "HybridChunker":
            # 根据提供者选择显示对应的模型名称
            if field_value == "Hugging Face":
                build_config["hf_model_name"]["show"] = True
                build_config["openai_model_name"]["show"] = False
            elif field_value == "OpenAI":
                build_config["hf_model_name"]["show"] = False
                build_config["openai_model_name"]["show"] = True

        return build_config

    # 将 LangChain Document 转换为 Data 对象
    def _docs_to_data(self, docs) -> list[Data]:
        return [Data(text=doc.page_content, data=doc.metadata) for doc in docs]

    # 执行文档分块操作
    def chunk_documents(self) -> DataFrame:
        # 提取 Docling 文档
        documents, warning = extract_docling_documents(self.data_inputs, self.doc_key)
        if warning:
            self.status = warning

        # 根据选择的分块器类型创建分块器实例
        chunker: BaseChunker
        if self.chunker == "HybridChunker":
            # 混合分块器：结合层级结构和 token 限制
            try:
                from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
            except ImportError as e:
                msg = (
                    "HybridChunker is not installed. Please install it with `uv pip install docling-core[chunking] "
                    "or `uv pip install transformers`"
                )
                raise ImportError(msg) from e
            max_tokens: int | None = self.max_tokens if self.max_tokens else None

            # 根据提供者选择分词器
            if self.provider == "Hugging Face":
                try:
                    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
                except ImportError as e:
                    msg = (
                        "HuggingFaceTokenizer is not installed."
                        " Please install it with `uv pip install docling-core[chunking]`"
                    )
                    raise ImportError(msg) from e
                tokenizer = HuggingFaceTokenizer.from_pretrained(
                    model_name=self.hf_model_name,
                    max_tokens=max_tokens,
                )
            elif self.provider == "OpenAI":
                try:
                    from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer
                except ImportError as e:
                    msg = (
                        "OpenAITokenizer is not installed."
                        " Please install it with `uv pip install docling-core[chunking]`"
                        " or `uv pip install transformers`"
                    )
                    raise ImportError(msg) from e
                if max_tokens is None:
                    # OpenAI 分词器需要设置上下文窗口长度
                    max_tokens = 128 * 1024  # context window length required for OpenAI tokenizers
                tokenizer = OpenAITokenizer(
                    tokenizer=tiktoken.encoding_for_model(self.openai_model_name), max_tokens=max_tokens
                )
            chunker = HybridChunker(
                tokenizer=tokenizer,
                merge_peers=bool(self.merge_peers),
                always_emit_headings=bool(self.always_emit_headings),
            )

        elif self.chunker == "HierarchicalChunker":
            # 层级分块器：基于文档结构进行分块
            chunker = HierarchicalChunker()
        else:
            msg = f"Unknown chunker: {self.chunker}"
            raise ValueError(msg)

        # 执行分块操作
        results: list[Data] = []
        try:
            for doc in documents:
                for chunk in chunker.chunk(dl_doc=doc):
                    # 获取上下文化文本
                    enriched_text = chunker.contextualize(chunk=chunk)
                    # 验证块元数据
                    meta = DocMeta.model_validate(chunk.meta)

                    results.append(
                        Data(
                            data={
                                "text": enriched_text,
                                "document_id": f"{doc.origin.binary_hash}",
                                "doc_items": json.dumps([item.self_ref for item in meta.doc_items]),
                            }
                        )
                    )

        except Exception as e:
            msg = f"Error splitting text: {e}"
            raise TypeError(msg) from e

        return DataFrame(results)
