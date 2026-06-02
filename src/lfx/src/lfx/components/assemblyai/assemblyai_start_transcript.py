# 标准库：文件路径处理
from pathlib import Path

# AssemblyAI SDK
import assemblyai as aai

# 组件基类、输入/输出定义、日志、数据模型
from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, DropdownInput, FileInput, MessageTextInput, Output, SecretStrInput
from lfx.log.logger import logger
from lfx.schema.data import Data


# AssemblyAI 转录任务创建组件，用于提交音频文件到 AssemblyAI 进行转录
class AssemblyAITranscriptionJobCreator(Component):
    display_name = "AssemblyAI Start Transcript"
    # 组件描述：使用 AssemblyAI 创建音频文件转录任务，支持高级选项
    description = "Create a transcription job for an audio file using AssemblyAI with advanced options"
    documentation = "https://www.assemblyai.com/docs"
    icon = "AssemblyAI"

    # 输入参数定义
    inputs = [
        # AssemblyAI API 密钥
        SecretStrInput(
            name="api_key",
            display_name="Assembly API Key",
            info="Your AssemblyAI API key. You can get one from https://www.assemblyai.com/",
            required=True,
        ),
        # 音频文件上传输入，支持多种音频格式
        FileInput(
            name="audio_file",
            display_name="Audio File",
            file_types=[
                "3ga",
                "8svx",
                "aac",
                "ac3",
                "aif",
                "aiff",
                "alac",
                "amr",
                "ape",
                "au",
                "dss",
                "flac",
                "flv",
                "m4a",
                "m4b",
                "m4p",
                "m4r",
                "mp3",
                "mpga",
                "ogg",
                "oga",
                "mogg",
                "opus",
                "qcp",
                "tta",
                "voc",
                "wav",
                "wma",
                "wv",
                "webm",
                "mts",
                "m2ts",
                "ts",
                "mov",
                "mp2",
                "mp4",
                "m4p",
                "m4v",
                "mxf",
            ],
            info="The audio file to transcribe",
            required=True,
        ),
        # 音频文件 URL（可替代文件上传）
        MessageTextInput(
            name="audio_file_url",
            display_name="Audio File URL",
            info="The URL of the audio file to transcribe (Can be used instead of a File)",
            advanced=True,
        ),
        # 语音模型选择：最佳模型或轻量模型
        DropdownInput(
            name="speech_model",
            display_name="Speech Model",
            options=[
                "best",
                "nano",
            ],
            value="best",
            info="The speech model to use for the transcription",
            advanced=True,
        ),
        # 自动语言检测开关
        BoolInput(
            name="language_detection",
            display_name="Automatic Language Detection",
            info="Enable automatic language detection",
            advanced=True,
        ),
        # 手动指定语言代码（当自动检测关闭时使用）
        MessageTextInput(
            name="language_code",
            display_name="Language",
            info=(
                """
            The language of the audio file. Can be set manually if automatic language detection is disabled.
            See https://www.assemblyai.com/docs/getting-started/supported-languages """
                "for a list of supported language codes."
            ),
            advanced=True,
        ),
        # 说话人标签（声纹分离）开关
        BoolInput(
            name="speaker_labels",
            display_name="Enable Speaker Labels",
            info="Enable speaker diarization",
        ),
        # 预期说话人数量（可选）
        MessageTextInput(
            name="speakers_expected",
            display_name="Expected Number of Speakers",
            info="Set the expected number of speakers (optional, enter a number)",
            advanced=True,
        ),
        # 自动标点符号开关
        BoolInput(
            name="punctuate",
            display_name="Punctuate",
            info="Enable automatic punctuation",
            advanced=True,
            value=True,
        ),
        # 文本格式化开关
        BoolInput(
            name="format_text",
            display_name="Format Text",
            info="Enable text formatting",
            advanced=True,
            value=True,
        ),
    ]

    # 输出参数：转录任务 ID
    outputs = [
        Output(display_name="Transcript ID", name="transcript_id", method="create_transcription_job"),
    ]

    # 创建转录任务
    def create_transcription_job(self) -> Data:
        aai.settings.api_key = self.api_key

        # Convert speakers_expected to int if it's not empty
        speakers_expected = None
        if self.speakers_expected and self.speakers_expected.strip():
            try:
                speakers_expected = int(self.speakers_expected)
            except ValueError:
                self.status = "Error: Expected Number of Speakers must be a valid integer"
                return Data(data={"error": "Error: Expected Number of Speakers must be a valid integer"})

        language_code = self.language_code or None

        config = aai.TranscriptionConfig(
            speech_model=self.speech_model,
            language_detection=self.language_detection,
            language_code=language_code,
            speaker_labels=self.speaker_labels,
            speakers_expected=speakers_expected,
            punctuate=self.punctuate,
            format_text=self.format_text,
        )

        audio = None
        if self.audio_file:
            if self.audio_file_url:
                logger.warning("Both an audio file an audio URL were specified. The audio URL was ignored.")

            # Check if the file exists
            if not Path(self.audio_file).exists():
                self.status = "Error: Audio file not found"
                return Data(data={"error": "Error: Audio file not found"})
            audio = self.audio_file
        elif self.audio_file_url:
            audio = self.audio_file_url
        else:
            self.status = "Error: Either an audio file or an audio URL must be specified"
            return Data(data={"error": "Error: Either an audio file or an audio URL must be specified"})

        try:
            transcript = aai.Transcriber().submit(audio, config=config)
        except Exception as e:  # noqa: BLE001
            logger.debug("Error submitting transcription job", exc_info=True)
            self.status = f"An error occurred: {e}"
            return Data(data={"error": f"An error occurred: {e}"})

        if transcript.error:
            self.status = transcript.error
            return Data(data={"error": transcript.error})
        result = Data(data={"transcript_id": transcript.id})
        self.status = result
        return result
