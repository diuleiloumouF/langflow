# YouTube 转录组件，从 YouTube 视频中提取字幕/转录文本
import re

import pandas as pd
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import DropdownInput, IntInput, MultilineInput
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.schema.message import Message
from lfx.template.field.base import Output


# YouTube 转录组件，提取视频的语音内容并支持多种输出格式
class YouTubeTranscriptsComponent(Component):
    """A component that extracts spoken content from YouTube videos as transcripts."""

    # 组件显示名称
    display_name: str = "YouTube Transcripts"
    # 组件描述
    description: str = "Extracts spoken content from YouTube videos with multiple output options."
    # 组件图标
    icon: str = "YouTube"
    # 组件内部名称
    name = "YouTubeTranscripts"

    # 组件输入参数定义
    inputs = [
        # YouTube 视频 URL
        MultilineInput(
            name="url",
            display_name="Video URL",
            info="Enter the YouTube video URL to get transcripts from.",
            tool_mode=True,
            required=True,
        ),
        # 转录分块大小（秒），每个分块包含的时间长度
        IntInput(
            name="chunk_size_seconds",
            display_name="Chunk Size (seconds)",
            value=60,
            info="The size of each transcript chunk in seconds.",
        ),
        # 翻译目标语言（可选）
        DropdownInput(
            name="translation",
            display_name="Translation Language",
            advanced=True,
            options=["", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "hi", "ar", "id"],
            info="Translate the transcripts to the specified language. Leave empty for no translation.",
        ),
    ]

    # 组件输出定义：DataFrame 格式、消息格式、数据格式
    outputs = [
        Output(name="dataframe", display_name="Chunks", method="get_dataframe_output"),
        Output(name="message", display_name="Transcript", method="get_message_output"),
        Output(name="data_output", display_name="Transcript + Source", method="get_data_output"),
    ]

    # 从 YouTube URL 中提取视频 ID
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)",
            r"youtube\.com\/watch\?.*?v=([^&\n?#]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        msg = f"Could not extract video ID from URL: {url}"
        raise ValueError(msg)

    # 从 YouTube 加载转录数据
    def _load_transcripts(self, *, as_chunks: bool = True):
        """Internal method to load transcripts from YouTube."""
        try:
            video_id = self._extract_video_id(self.url)
        except ValueError as e:
            msg = f"Invalid YouTube URL: {e}"
            raise ValueError(msg) from e

        try:
            # Use new v1.0+ API - create instance
            # 使用 v1.0+ 新版 API 创建实例
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)

            # Get transcript in specified language or default to English
            if self.translation:
                # Get any available transcript and translate it
                # 获取可用字幕并翻译为目标语言
                transcript = transcript_list.find_transcript(["en"])
                transcript = transcript.translate(self.translation)
            else:
                # Try to get transcript in available languages
                try:
                    transcript = transcript_list.find_transcript(["en"])
                except NoTranscriptFound:
                    # Try auto-generated English
                    # 尝试获取自动生成的英文字幕
                    transcript = transcript_list.find_generated_transcript(["en"])

            # Fetch the transcript data
            transcript_data = api.fetch(transcript.video_id, [transcript.language_code])

        except (TranscriptsDisabled, NoTranscriptFound) as e:
            error_type = type(e).__name__
            msg = (
                f"Could not retrieve transcripts for video '{video_id}'. "
                "Possible reasons:\n"
                "1. This video does not have captions/transcripts enabled\n"
                "2. The video is private, restricted, or deleted\n"
                f"\nTechnical error ({error_type}): {e}"
            )
            raise RuntimeError(msg) from e
        except Exception as e:
            error_type = type(e).__name__
            msg = (
                f"Could not retrieve transcripts for video '{video_id}'. "
                "Possible reasons:\n"
                "1. This video does not have captions/transcripts enabled\n"
                "2. The video is private, restricted, or deleted\n"
                "3. YouTube is blocking automated requests\n"
                f"\nTechnical error ({error_type}): {e}"
            )
            raise RuntimeError(msg) from e

        if as_chunks:
            # Group into chunks based on chunk_size_seconds
            # 按时间窗口分块
            return self._chunk_transcript(transcript_data)
        # Return as continuous text
        return transcript_data

    # 将转录片段按时间窗口分组为块
    def _chunk_transcript(self, transcript_data):
        """Group transcript segments into time-based chunks."""
        chunks = []
        current_chunk = []
        chunk_start = 0

        for segment in transcript_data:
            # Handle both dict (old API) and object (new API) formats
            # 兼容新旧 API 格式
            segment_start = segment.start if hasattr(segment, "start") else segment["start"]

            # If this segment starts beyond the current chunk window, start a new chunk
            # 如果当前片段超出当前块的时间窗口，则开始新的块
            if segment_start - chunk_start >= self.chunk_size_seconds and current_chunk:
                chunk_text = " ".join(s.text if hasattr(s, "text") else s["text"] for s in current_chunk)
                chunks.append({"start": chunk_start, "text": chunk_text})
                current_chunk = []
                chunk_start = segment_start

            current_chunk.append(segment)

        # Add the last chunk
        if current_chunk:
            chunk_text = " ".join(s.text if hasattr(s, "text") else s["text"] for s in current_chunk)
            chunks.append({"start": chunk_start, "text": chunk_text})

        return chunks

    # 以 DataFrame 格式输出转录内容（包含时间戳和文本列）
    def get_dataframe_output(self) -> DataFrame:
        """Provides transcript output as a DataFrame with timestamp and text columns."""
        try:
            chunks = self._load_transcripts(as_chunks=True)

            # Create DataFrame with timestamp and text columns
            data = []
            for chunk in chunks:
                start_seconds = int(chunk["start"])
                start_minutes = start_seconds // 60
                start_seconds_remainder = start_seconds % 60
                timestamp = f"{start_minutes:02d}:{start_seconds_remainder:02d}"
                data.append({"timestamp": timestamp, "text": chunk["text"]})

            return DataFrame(pd.DataFrame(data))

        except (TranscriptsDisabled, NoTranscriptFound, RuntimeError, ValueError) as exc:
            error_msg = f"Failed to get YouTube transcripts: {exc!s}"
            return DataFrame(pd.DataFrame({"error": [error_msg]}))

    # 以连续文本消息格式输出转录内容
    def get_message_output(self) -> Message:
        """Provides transcript output as continuous text."""
        try:
            transcript_data = self._load_transcripts(as_chunks=False)
            # Handle both dict (old API) and object (new API) formats
            # 兼容新旧 API 格式，拼接所有文本
            result = " ".join(
                segment.text if hasattr(segment, "text") else segment["text"] for segment in transcript_data
            )
            return Message(text=result)

        except (TranscriptsDisabled, NoTranscriptFound, RuntimeError, ValueError) as exc:
            error_msg = f"Failed to get YouTube transcripts: {exc!s}"
            return Message(text=error_msg)

    # 以结构化 Data 对象输出转录内容和元数据
    def get_data_output(self) -> Data:
        """创建包含转录文本和元数据的结构化数据对象。

        Creates a structured data object with transcript and metadata.

        Returns a Data object containing transcript text, video URL, and any error
        messages that occurred during processing. The object includes:
        - 'transcript': continuous text from the entire video (concatenated if multiple parts)
        - 'video_url': the input YouTube URL
        - 'error': error message if an exception occurs
        """
        default_data = {"transcript": "", "video_url": self.url, "error": None}

        try:
            transcript_data = self._load_transcripts(as_chunks=False)
            if not transcript_data:
                default_data["error"] = "No transcripts found."
                return Data(data=default_data)

            # Combine all transcript segments - handle both dict and object formats
            # 合并所有转录片段，兼容新旧 API 格式
            full_transcript = " ".join(
                segment.text if hasattr(segment, "text") else segment["text"] for segment in transcript_data
            )
            return Data(data={"transcript": full_transcript, "video_url": self.url})

        except (TranscriptsDisabled, NoTranscriptFound, RuntimeError, ValueError) as exc:
            default_data["error"] = str(exc)
            return Data(data=default_data)
