# AssemblyAI SDK
import assemblyai as aai

# 组件基类、输入/输出定义、日志、数据模型
from lfx.custom.custom_component.component import Component
from lfx.field_typing.range_spec import RangeSpec
from lfx.io import DataInput, FloatInput, Output, SecretStrInput
from lfx.log.logger import logger
from lfx.schema.data import Data


# AssemblyAI 转录任务轮询组件，用于查询转录任务状态直到完成
class AssemblyAITranscriptionJobPoller(Component):
    display_name = "AssemblyAI Poll Transcript"
    # 组件描述：使用 AssemblyAI 轮询转录任务的状态
    description = "Poll for the status of a transcription job using AssemblyAI"
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
        # 要轮询的转录任务 ID
        DataInput(
            name="transcript_id",
            display_name="Transcript ID",
            info="The ID of the transcription job to poll",
            required=True,
        ),
        # 轮询间隔（秒），范围 3-30
        FloatInput(
            name="polling_interval",
            display_name="Polling Interval",
            value=3.0,
            info="The polling interval in seconds",
            advanced=True,
            range_spec=RangeSpec(min=3, max=30),
        ),
    ]

    # 输出参数：转录结果
    outputs = [
        Output(display_name="Transcription Result", name="transcription_result", method="poll_transcription_job"),
    ]

    # 轮询转录任务状态直到完成并返回结果
    def poll_transcription_job(self) -> Data:
        """Polls the transcription status until completion and returns the Data."""
        aai.settings.api_key = self.api_key
        aai.settings.polling_interval = self.polling_interval

        # check if it's an error message from the previous step
        if self.transcript_id.data.get("error"):
            self.status = self.transcript_id.data["error"]
            return self.transcript_id

        try:
            transcript = aai.Transcript.get_by_id(self.transcript_id.data["transcript_id"])
        except Exception as e:  # noqa: BLE001
            error = f"Getting transcription failed: {e}"
            logger.debug(error, exc_info=True)
            self.status = error
            return Data(data={"error": error})

        if transcript.status == aai.TranscriptStatus.completed:
            json_response = transcript.json_response
            text = json_response.pop("text", None)
            utterances = json_response.pop("utterances", None)
            transcript_id = json_response.pop("id", None)
            sorted_data = {"text": text, "utterances": utterances, "id": transcript_id}
            sorted_data.update(json_response)
            data = Data(data=sorted_data)
            self.status = data
            return data
        self.status = transcript.error
        return Data(data={"error": transcript.error})
