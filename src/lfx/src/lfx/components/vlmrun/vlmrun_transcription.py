# VLM Run 转录组件，使用 VLM Run AI 从音视频文件中提取结构化数据
from pathlib import Path
from urllib.parse import urlparse

from langflow.custom.custom_component.component import Component
from langflow.io import (
    DropdownInput,
    FileInput,
    IntInput,
    MessageTextInput,
    Output,
    SecretStrInput,
)
from langflow.schema.data import Data
from loguru import logger


# 使用 VLM Run AI 从音频和视频中提取结构化转录数据的组件
class VLMRunTranscription(Component):
    # 组件显示名称
    display_name = "VLM Run Transcription"
    # 组件描述
    description = "Extract structured data from audio and video using [VLM Run AI](https://app.vlm.run)"
    # 文档链接
    documentation = "https://docs.vlm.run"
    # 组件图标
    icon = "VLMRun"
    # 标记为 Beta 功能
    beta = True

    # 组件输入参数定义
    inputs = [
        # VLM Run API 密钥
        SecretStrInput(
            name="api_key",
            display_name="VLM Run API Key",
            info="Get your API key from https://app.vlm.run",
            required=True,
        ),
        # 媒体类型：音频或视频
        DropdownInput(
            name="media_type",
            display_name="Media Type",
            options=["audio", "video"],
            value="audio",
            info="Select the type of media to process",
        ),
        # 上传的媒体文件列表（支持多种音视频格式）
        FileInput(
            name="media_files",
            display_name="Media Files",
            file_types=[
                "mp3",
                "wav",
                "m4a",
                "flac",
                "ogg",
                "opus",
                "webm",
                "aac",
                "mp4",
                "mov",
                "avi",
                "mkv",
                "flv",
                "wmv",
                "m4v",
            ],
            info="Upload one or more audio/video files",
            required=False,
            is_list=True,
        ),
        # 媒体文件 URL（替代文件上传方式）
        MessageTextInput(
            name="media_url",
            display_name="Media URL",
            info="URL to media file (alternative to file upload)",
            required=False,
            advanced=True,
        ),
        # 处理超时时间（秒）
        IntInput(
            name="timeout_seconds",
            display_name="Timeout (seconds)",
            value=600,
            info="Maximum time to wait for processing completion",
            advanced=True,
        ),
        # 处理领域，当前仅支持转录
        DropdownInput(
            name="domain",
            display_name="Processing Domain",
            options=["transcription"],
            value="transcription",
            info="Select the processing domain",
            advanced=True,
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(
            display_name="Result",
            name="result",
            method="process_media",
        ),
    ]

    # 验证输入参数，确保提供了媒体文件或 URL
    def _check_inputs(self) -> str | None:
        """Validate that either media files or URL is provided."""
        if not self.media_files and not self.media_url:
            return "Either media files or media URL must be provided"
        return None

    # 导入并返回 VLMRun 客户端类
    def _import_vlmrun(self):
        """Import and return VLMRun client class."""
        try:
            from vlmrun.client import VLMRun
        except ImportError as e:
            error_msg = "VLM Run SDK not installed. Run: pip install 'vlmrun[all]'"
            raise ImportError(error_msg) from e
        else:
            return VLMRun

    # 根据媒体类型生成 API 请求响应
    def _generate_media_response(self, client, media_source):
        """Generate response for audio or video media."""
        domain_str = f"{self.media_type}.{self.domain}"

        if self.media_type == "audio":
            if isinstance(media_source, Path):
                return client.audio.generate(file=media_source, domain=domain_str, batch=True)
            return client.audio.generate(url=media_source, domain=domain_str, batch=True)
        # video
        if isinstance(media_source, Path):
            return client.video.generate(file=media_source, domain=domain_str, batch=True)
        return client.video.generate(url=media_source, domain=domain_str, batch=True)

    # 等待批量处理完成
    def _wait_for_response(self, client, response):
        """Wait for batch processing to complete if needed."""
        if hasattr(response, "id"):
            return client.predictions.wait(response.id, timeout=self.timeout_seconds)
        return response

    # 从分段数据中提取转录文本
    def _extract_transcription(self, segments: list) -> list[str]:
        """Extract transcription parts from segments."""
        transcription_parts = []
        for segment in segments:
            if self.media_type == "audio" and "audio" in segment:
                transcription_parts.append(segment["audio"].get("content", ""))
            elif self.media_type == "video" and "video" in segment:
                transcription_parts.append(segment["video"].get("content", ""))
                # Also include audio if available for video
                # 视频类型同时包含音频内容
                if "audio" in segment:
                    audio_content = segment["audio"].get("content", "")
                    if audio_content and audio_content.strip():
                        transcription_parts.append(f"[Audio: {audio_content}]")
        return transcription_parts

    # 创建标准化的结果字典
    def _create_result_dict(self, response, transcription_parts: list, source_name: str) -> dict:
        """Create a standardized result dictionary."""
        response_data = response.response if hasattr(response, "response") else {}
        result = {
            "prediction_id": response.id if hasattr(response, "id") else None,
            "transcription": " ".join(transcription_parts),
            "full_response": response_data,
            "metadata": {
                "media_type": self.media_type,
                "duration": response_data.get("metadata", {}).get("duration", 0),
            },
            "usage": response.usage if hasattr(response, "usage") else None,
            "status": response.status if hasattr(response, "status") else "completed",
        }

        # Add source-specific field
        # 根据来源类型添加对应的字段（URL 或文件名）
        parsed_url = urlparse(source_name)
        if parsed_url.scheme in ["http", "https", "s3", "gs", "ftp", "ftps"]:
            result["source"] = source_name
        else:
            result["filename"] = source_name

        return result

    # 处理单个媒体文件或 URL
    def _process_single_media(self, client, media_source, source_name: str) -> dict:
        """Process a single media file or URL."""
        response = self._generate_media_response(client, media_source)
        response = self._wait_for_response(client, response)
        response_data = response.response if hasattr(response, "response") else {}
        segments = response_data.get("segments", [])
        transcription_parts = self._extract_transcription(segments)
        return self._create_result_dict(response, transcription_parts, source_name)

    # 处理音频或视频文件并提取结构化数据（主入口方法）
    def process_media(self) -> Data:
        """Process audio or video file and extract structured data."""
        # Validate inputs
        error_msg = self._check_inputs()
        if error_msg:
            self.status = error_msg
            return Data(data={"error": error_msg})

        try:
            # Import and initialize client
            vlmrun_class = self._import_vlmrun()
            client = vlmrun_class(api_key=self.api_key)
            all_results = []

            # Handle multiple files
            # 处理多个上传的文件
            if self.media_files:
                files_to_process = self.media_files if isinstance(self.media_files, list) else [self.media_files]
                for idx, media_file in enumerate(files_to_process):
                    self.status = f"Processing file {idx + 1} of {len(files_to_process)}..."
                    result = self._process_single_media(client, Path(media_file), Path(media_file).name)
                    all_results.append(result)

            # Handle URL
            # 处理 URL 方式的媒体源
            elif self.media_url:
                result = self._process_single_media(client, self.media_url, self.media_url)
                all_results.append(result)

            # Return clean, flexible output structure
            # 返回简洁灵活的输出结构
            output_data = {
                "results": all_results,
                "total_files": len(all_results),
            }
            self.status = f"Successfully processed {len(all_results)} file(s)"
            return Data(data=output_data)

        except ImportError as e:
            self.status = str(e)
            return Data(data={"error": str(e)})
        except (ValueError, ConnectionError, TimeoutError) as e:
            logger.opt(exception=True).debug("Error processing media with VLM Run")
            error_msg = f"Processing failed: {e!s}"
            self.status = error_msg
            return Data(data={"error": error_msg})
        except (AttributeError, KeyError, OSError) as e:
            logger.opt(exception=True).debug("Unexpected error processing media with VLM Run")
            error_msg = f"Unexpected error: {e!s}"
            self.status = error_msg
            return Data(data={"error": error_msg})
