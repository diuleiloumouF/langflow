# 类型注解支持
from typing import Any

# Docling 图片引用模式
from docling_core.types.doc import ImageRefMode

# Docling 文档提取工具函数
from lfx.base.data.docling_utils import extract_docling_documents

# 组件基类
from lfx.custom import Component

# 输入组件类型
from lfx.io import DropdownInput, HandleInput, MessageTextInput, Output, StrInput

# 数据模型
from lfx.schema import Data, DataFrame


# Docling 文档导出组件，将 DoclingDocument 导出为 Markdown、HTML 等格式
class ExportDoclingDocumentComponent(Component):
    display_name: str = "Export DoclingDocument"
    description: str = "Export DoclingDocument to markdown, html or other formats."
    documentation = "https://docling-project.github.io/docling/"
    icon = "Docling"
    name = "ExportDoclingDocument"

    # 输入参数定义
    inputs = [
        # 输入数据：包含待导出的文档
        HandleInput(
            name="data_inputs",
            display_name="JSON or Table",
            info="The data with documents to export.",
            input_types=["Data", "JSON", "DataFrame", "Table"],
            required=True,
        ),
        # 导出格式选择
        DropdownInput(
            name="export_format",
            display_name="Export format",
            options=["Markdown", "HTML", "Plaintext", "DocTags"],
            info="Select the export format to convert the input.",
            value="Markdown",
            real_time_refresh=True,
        ),
        # 图片导出模式：占位符或嵌入
        DropdownInput(
            name="image_mode",
            display_name="Image export mode",
            options=["placeholder", "embedded"],
            info=(
                "Specify how images are exported in the output. Placeholder will replace the images with a string, "
                "whereas Embedded will include them as base64 encoded images."
            ),
            value="placeholder",
        ),
        # Markdown 导出的图片占位符文本
        StrInput(
            name="md_image_placeholder",
            display_name="Image placeholder",
            info="Specify the image placeholder for markdown exports.",
            value="<!-- image -->",
            advanced=True,
        ),
        # Markdown 导出的分页占位符文本
        StrInput(
            name="md_page_break_placeholder",
            display_name="Page break placeholder",
            info="Add this placeholder betweek pages in the markdown output.",
            value="",
            advanced=True,
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

    # 输出参数定义
    outputs = [
        Output(display_name="Exported data", name="data", method="export_document"),
        Output(display_name="Table", name="dataframe", method="as_dataframe"),
    ]

    # 根据导出格式动态更新构建配置
    def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        if field_name == "export_format" and field_value == "Markdown":
            # Markdown 格式：显示图片和分页占位符配置
            build_config["md_image_placeholder"]["show"] = True
            build_config["md_page_break_placeholder"]["show"] = True
            build_config["image_mode"]["show"] = True
        elif field_name == "export_format" and field_value == "HTML":
            # HTML 格式：仅显示图片模式配置
            build_config["md_image_placeholder"]["show"] = False
            build_config["md_page_break_placeholder"]["show"] = False
            build_config["image_mode"]["show"] = True
        elif field_name == "export_format" and field_value in {"Plaintext", "DocTags"}:
            # 纯文本/DocTags 格式：隐藏所有图片相关配置
            build_config["md_image_placeholder"]["show"] = False
            build_config["md_page_break_placeholder"]["show"] = False
            build_config["image_mode"]["show"] = False

        return build_config

    # 导出文档为指定格式
    def export_document(self) -> list[Data]:
        # 提取 Docling 文档
        documents, warning = extract_docling_documents(self.data_inputs, self.doc_key)
        if warning:
            self.status = warning

        # 根据导出格式转换文档
        results: list[Data] = []
        try:
            image_mode = ImageRefMode(self.image_mode)
            for doc in documents:
                content = ""
                if self.export_format == "Markdown":
                    content = doc.export_to_markdown(
                        image_mode=image_mode,
                        image_placeholder=self.md_image_placeholder,
                        page_break_placeholder=self.md_page_break_placeholder,
                    )
                elif self.export_format == "HTML":
                    content = doc.export_to_html(image_mode=image_mode)
                elif self.export_format == "Plaintext":
                    content = doc.export_to_text()
                elif self.export_format == "DocTags":
                    content = doc.export_to_doctags()

                # 保留 DoclingDocument 的元数据
                metadata: dict = {"export_format": self.export_format}
                if hasattr(doc, "name") and doc.name:
                    metadata["name"] = doc.name
                if hasattr(doc, "origin") and doc.origin is not None:
                    if hasattr(doc.origin, "filename") and doc.origin.filename:
                        metadata["filename"] = doc.origin.filename
                    if hasattr(doc.origin, "binary_hash") and doc.origin.binary_hash:
                        metadata["document_id"] = str(doc.origin.binary_hash)
                    if hasattr(doc.origin, "mimetype") and doc.origin.mimetype:
                        metadata["mimetype"] = doc.origin.mimetype

                results.append(Data(text=content, data={"text": content, **metadata}))
        except Exception as e:
            msg = f"Error splitting text: {e}"
            raise TypeError(msg) from e

        return results

    # 将导出结果转换为 DataFrame 格式
    def as_dataframe(self) -> DataFrame:
        return DataFrame(self.export_document())
