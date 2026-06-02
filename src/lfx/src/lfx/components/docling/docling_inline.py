# JSON 序列化
import json

# 子进程管理
import subprocess

# 系统模块
import sys

# 文本清理
import textwrap

# 时间处理
import time

# 文件组件基类
from lfx.base.data import BaseFileComponent

# Pydantic 模型序列化工具
from lfx.base.data.docling_utils import _serialize_pydantic_model

# 输入组件类型
from lfx.inputs import BoolInput, DropdownInput, HandleInput, StrInput

# 数据模型
from lfx.schema import Data


# Docling 内联组件，在本地运行 Docling 模型处理输入文档
class DoclingInlineComponent(BaseFileComponent):
    display_name = "Docling"
    description = "Uses Docling to process input documents running the Docling models locally."
    documentation = "https://docling-project.github.io/docling/"
    trace_type = "tool"
    icon = "Docling"
    name = "DoclingInline"

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
        # Docling 处理管道类型：标准管道或 VLM 管道
        DropdownInput(
            name="pipeline",
            display_name="Pipeline",
            info="Docling pipeline to use",
            options=["standard", "vlm"],
            value="standard",
        ),
        # OCR 引擎选择：None 表示禁用 OCR
        DropdownInput(
            name="ocr_engine",
            display_name="OCR Engine",
            info="OCR engine to use. None will disable OCR.",
            options=["None", "easyocr", "tesserocr", "rapidocr", "ocrmac"],
            value="None",
        ),
        # 是否启用图片分类
        BoolInput(
            name="do_picture_classification",
            display_name="Picture classification",
            info="If enabled, the Docling pipeline will classify the pictures type.",
            value=False,
        ),
        # 图片描述使用的语言模型（可选）
        HandleInput(
            name="pic_desc_llm",
            display_name="Picture description LLM",
            info="If connected, the model to use for running the picture description task.",
            input_types=["LanguageModel"],
            required=False,
        ),
        # 图片描述的提示词
        StrInput(
            name="pic_desc_prompt",
            display_name="Picture description prompt",
            value="Describe the image in three sentences. Be concise and accurate.",
            info="The user prompt to use when invoking the model.",
            advanced=True,
        ),
        # TODO: expose more Docling options
    ]

    # 输出参数定义
    outputs = [
        *BaseFileComponent.get_base_outputs(),
    ]

    # ------------------------------------------------------------------ #
    # 在独立 OS 进程中运行 Docling 的子脚本。                              #
    # 使用 subprocess.Popen（与 Read File 高级模式相同的模式）              #
    # 而非 multiprocessing/threading，原因如下：                           #
    #   1. 在 Gunicorn 的 fork 模式 worker 下可靠工作                      #
    #   2. 父进程的事件循环保持空闲，可用于 SSE 心跳                        #
    #   3. 避免 pickle / 信号处理器冲突                                    #
    # ------------------------------------------------------------------ #
    _CHILD_SCRIPT: str = textwrap.dedent(r"""
        import json, sys

        def main():
            cfg = json.loads(sys.stdin.read())
            file_paths      = cfg["file_paths"]
            pipeline        = cfg["pipeline"]
            ocr_engine      = cfg["ocr_engine"]
            do_picture_cls  = cfg["do_picture_classification"]
            pic_desc_config = cfg.get("pic_desc_config")
            pic_desc_prompt = cfg.get("pic_desc_prompt", "")

            try:
                from docling.datamodel.base_models import ConversionStatus, InputFormat
                from docling.datamodel.pipeline_options import PdfPipelineOptions
                from docling.document_converter import DocumentConverter, FormatOption, PdfFormatOption
            except ImportError as e:
                print(json.dumps({"ok": False, "error": f"Docling is not installed: {e}"}))
                return

            # --- 构建转换器 ------------------------------------------------
            try:
                pipe = PdfPipelineOptions()
                pipe.do_ocr = ocr_engine not in ("", "None")
                if pipe.do_ocr:
                    try:
                        from docling.models.factories import get_ocr_factory
                        fac = get_ocr_factory(allow_external_plugins=False)
                        pipe.ocr_options = fac.create_options(kind=ocr_engine)
                    except Exception:
                        pipe.do_ocr = False

                pipe.do_picture_classification = do_picture_cls

                if pic_desc_config:
                    try:
                        import importlib
                        from pydantic import TypeAdapter
                        from langchain_docling.picture_description import (
                            PictureDescriptionLangChainOptions,
                        )
                        mod_name, cls_name = pic_desc_config["__class_path__"].rsplit(".", 1)
                        mod = importlib.import_module(mod_name)
                        cls = getattr(mod, cls_name)
                        adapter = TypeAdapter(cls)
                        llm = adapter.validate_python(pic_desc_config["config"])
                        pipe.do_picture_description = True
                        pipe.allow_external_plugins = True
                        pipe.picture_description_options = PictureDescriptionLangChainOptions(
                            llm=llm, prompt=pic_desc_prompt,
                        )
                    except Exception as e:
                        print(json.dumps({"ok": False, "error": f"Picture description setup failed: {e}"}))
                        return

                if pipeline == "vlm":
                    try:
                        from docling.datamodel.pipeline_options import VlmPipelineOptions
                        from docling.pipeline.vlm_pipeline import VlmPipeline
                        vlm_opts = VlmPipelineOptions()
                        if sys.platform == "darwin":
                            try:
                                from docling.datamodel.vlm_model_specs import GRANITEDOCLING_MLX
                                vlm_opts.vlm_options = GRANITEDOCLING_MLX
                            except ImportError:
                                from docling.datamodel.vlm_model_specs import GRANITEDOCLING_TRANSFORMERS
                                vlm_opts.vlm_options = GRANITEDOCLING_TRANSFORMERS
                        fmt = {}
                        if hasattr(InputFormat, "PDF"):
                            fmt[InputFormat.PDF] = PdfFormatOption(
                                pipeline_cls=VlmPipeline, pipeline_options=vlm_opts,
                            )
                        if hasattr(InputFormat, "IMAGE"):
                            fmt[InputFormat.IMAGE] = PdfFormatOption(
                                pipeline_cls=VlmPipeline, pipeline_options=vlm_opts,
                            )
                        converter = DocumentConverter(format_options=fmt)
                    except Exception as e:
                        print(json.dumps({"ok": False, "error": f"VLM pipeline setup failed: {e}"}))
                        return
                else:
                    pdf_opt = PdfFormatOption(pipeline_options=pipe)
                    fmt = {}
                    if hasattr(InputFormat, "PDF"):
                        fmt[InputFormat.PDF] = pdf_opt
                    if hasattr(InputFormat, "IMAGE"):
                        fmt[InputFormat.IMAGE] = pdf_opt
                    converter = DocumentConverter(format_options=fmt)
            except Exception as e:
                print(json.dumps({"ok": False, "error": f"Converter creation failed: {e}"}))
                return

            # --- 处理文件 --------------------------------------------------
            results = []
            for fp in file_paths:
                try:
                    res = converter.convert(fp)
                    ok = False
                    if hasattr(res, "status"):
                        try:
                            ok = res.status == ConversionStatus.SUCCESS
                        except Exception:
                            ok = str(res.status).lower() == "success"
                    if not ok and getattr(res, "document", None) is not None:
                        ok = True
                    if ok and res.document is not None:
                        doc_json = res.document.export_to_dict()
                        results.append({
                            "document": doc_json,
                            "file_path": str(fp),
                            "status": "SUCCESS",
                        })
                    else:
                        results.append(None)
                except Exception as e:
                    sys.stderr.write(f"Error processing {fp}: {e}\n")
                    results.append(None)

            print(json.dumps({"ok": True, "results": results}))

        if __name__ == "__main__":
            main()
    """)

    # 处理文件列表
    def process_files(self, file_list: list[BaseFileComponent.BaseFile]) -> list[BaseFileComponent.BaseFile]:
        # 仅检查 docling 是否已安装，不实际导入
        # 实际导入（PyTorch、transformers 等）发生在子进程中
        # 在此处导入会增加内存消耗，可能导致 Gunicorn worker 被 OOM 杀死
        import importlib.util

        if importlib.util.find_spec("docling") is None:
            msg = (
                "Docling is an optional dependency. Install with `uv pip install 'langflow[docling]'` or refer to the "
                "documentation on how to install optional dependencies."
            )
            raise ImportError(msg)

        # 收集有效的文件路径
        file_paths = [str(file.path) for file in file_list if file.path]

        if not file_paths:
            self.log("No files to process.")
            return file_list

        # 序列化图片描述 LLM 配置
        pic_desc_config: dict | None = None
        if self.pic_desc_llm is not None:
            pic_desc_config = _serialize_pydantic_model(self.pic_desc_llm)

        # 构建传递给子进程的参数
        args = {
            "file_paths": file_paths,
            "pipeline": self.pipeline,
            "ocr_engine": self.ocr_engine,
            "do_picture_classification": self.do_picture_classification,
            "pic_desc_config": pic_desc_config,
            "pic_desc_prompt": self.pic_desc_prompt,
        }

        # 使用 Popen 和轮询循环（与 Read File 高级模式相同的模式）
        # 这避免了 Gunicorn 下的多进程/线程问题，并通过定期心跳日志保持 SSE 事件流活跃
        docling_timeout = 600  # 10 分钟
        poll_interval = 5

        # 使用临时文件存储 stdout，避免管道缓冲区死锁
        # Docling（及其传递依赖：PyTorch、transformers 等）可能产生大量输出
        # 使用 subprocess.PIPE 时，操作系统管道缓冲区（macOS 上约 16KB）会填满，
        # 子进程阻塞在写入上，而父进程在子进程退出后才读取，导致永久等待
        import tempfile

        with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
            proc = subprocess.Popen(  # noqa: S603
                [sys.executable, "-u", "-c", self._CHILD_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=stdout_file,
                stderr=stderr_file,
            )
            # 通过 stdin 传递参数给子进程
            proc.stdin.write(json.dumps(args).encode("utf-8"))
            proc.stdin.close()

            # 轮询等待子进程完成
            start = time.monotonic()
            while proc.poll() is None:
                elapsed = time.monotonic() - start
                # 检查是否超时
                if elapsed >= docling_timeout:
                    proc.kill()
                    proc.wait()
                    msg = (
                        f"Docling processing timed out after {docling_timeout}s. Try processing fewer or smaller files."
                    )
                    raise TimeoutError(msg)
                self.log(f"Docling processing in progress ({int(elapsed)}s elapsed)...")
                time.sleep(poll_interval)

            # 读取子进程的输出
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout_bytes = stdout_file.read()
            stderr_bytes = stderr_file.read()

        # 检查子进程是否有输出
        if not stdout_bytes:
            err_msg = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else "no output"
            msg = f"Docling subprocess error: {err_msg}"
            raise RuntimeError(msg)

        # 解析子进程返回的 JSON 结果
        try:
            payload = json.loads(stdout_bytes.decode("utf-8"))
        except Exception as e:
            err_msg = stderr_bytes.decode("utf-8", errors="replace")
            msg = f"Invalid JSON from Docling subprocess: {e}. stderr={err_msg}"
            raise RuntimeError(msg) from e

        # 检查子进程是否成功
        if not payload.get("ok"):
            error_msg = payload.get("error", "Unknown Docling error")
            if "not installed" in error_msg.lower():
                raise ImportError(error_msg)
            raise RuntimeError(error_msg)

        # 从子进程返回的 JSON 字典重建 DoclingDocument 对象
        from docling_core.types.doc import DoclingDocument

        raw_results = payload.get("results", [])
        processed_data: list[Data | None] = []
        for r in raw_results:
            if r is None:
                processed_data.append(None)
                continue
            try:
                doc = DoclingDocument.model_validate(r["document"])
            except Exception:  # noqa: BLE001
                # 如果验证失败，回退到保留原始字典
                doc = r["document"]
            processed_data.append(Data(data={"doc": doc, "file_path": r["file_path"]}))

        return self.rollup_data(file_list, processed_data)
