# AssemblyAI SDK
import assemblyai as aai

# 组件基类、输入/输出定义、日志、数据模型
from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, DropdownInput, FloatInput, IntInput, MultilineInput, Output, SecretStrInput
from lfx.log.logger import logger
from lfx.schema.data import Data


# AssemblyAI LeMUR 组件，使用 AssemblyAI LeMUR 框架将大语言模型应用于语音数据
class AssemblyAILeMUR(Component):
    display_name = "AssemblyAI LeMUR"
    # 组件描述：使用 AssemblyAI LeMUR 框架将大语言模型应用于语音数据
    description = "Apply Large Language Models to spoken data using the AssemblyAI LeMUR framework"
    documentation = "https://www.assemblyai.com/docs/lemur"
    icon = "AssemblyAI"

    # 输入参数定义
    inputs = [
        # AssemblyAI API 密钥
        SecretStrInput(
            name="api_key",
            display_name="Assembly API Key",
            info="Your AssemblyAI API key. You can get one from https://www.assemblyai.com/",
            advanced=False,
            required=True,
        ),
        # 转录结果数据输入
        DataInput(
            name="transcription_result",
            display_name="Transcription Result",
            info="The transcription result from AssemblyAI",
            required=True,
        ),
        # LLM 提示词输入（多行文本）
        MultilineInput(name="prompt", display_name="Input Prompt", info="The text to prompt the model", required=True),
        # 最终使用的 LLM 模型（压缩后执行最终提示的模型）
        DropdownInput(
            name="final_model",
            display_name="Final Model",
            options=["claude3_5_sonnet", "claude3_opus", "claude3_haiku", "claude3_sonnet"],
            value="claude3_5_sonnet",
            info="The model that is used for the final prompt after compression is performed",
            advanced=True,
        ),
        # 模型温度参数，控制输出随机性
        FloatInput(
            name="temperature",
            display_name="Temperature",
            advanced=True,
            value=0.0,
            info="The temperature to use for the model",
        ),
        # 最大输出 token 数量
        IntInput(
            name="max_output_size",
            display_name=" Max Output Size",
            advanced=True,
            value=2000,
            info="Max output size in tokens, up to 4000",
        ),
        # LeMUR 端点选择：任务、摘要、问答
        DropdownInput(
            name="endpoint",
            display_name="Endpoint",
            options=["task", "summary", "question-answer"],
            value="task",
            info=(
                "The LeMUR endpoint to use. For 'summary' and 'question-answer',"
                " no prompt input is needed. See https://www.assemblyai.com/docs/api-reference/lemur/ for more info."
            ),
            advanced=True,
        ),
        # 问答模式下的问题列表（逗号分隔）
        MultilineInput(
            name="questions",
            display_name="Questions",
            info="Comma-separated list of your questions. Only used if Endpoint is 'question-answer'",
            advanced=True,
        ),
        # 转录 ID 列表（逗号分隔），可同时处理多个转录
        MultilineInput(
            name="transcript_ids",
            display_name="Transcript IDs",
            info=(
                "Comma-separated list of transcript IDs. LeMUR can perform actions over multiple transcripts."
                " If provided, the Transcription Result is ignored."
            ),
            advanced=True,
        ),
    ]

    # 输出参数：LeMUR 处理结果
    outputs = [
        Output(display_name="LeMUR Response", name="lemur_response", method="run_lemur"),
    ]

    # 运行 LeMUR 任务端点，输入 LLM 提示词
    def run_lemur(self) -> Data:
        """Use the LeMUR task endpoint to input the LLM prompt."""
        aai.settings.api_key = self.api_key

        if not self.transcription_result and not self.transcript_ids:
            error = "Either a Transcription Result or Transcript IDs must be provided"
            self.status = error
            return Data(data={"error": error})
        if self.transcription_result and self.transcription_result.data.get("error"):
            # error message from the previous step
            self.status = self.transcription_result.data["error"]
            return self.transcription_result
        if self.endpoint == "task" and not self.prompt:
            self.status = "No prompt specified for the task endpoint"
            return Data(data={"error": "No prompt specified"})
        if self.endpoint == "question-answer" and not self.questions:
            error = "No Questions were provided for the question-answer endpoint"
            self.status = error
            return Data(data={"error": error})

        # Check for valid transcripts
        transcript_ids = None
        if self.transcription_result and "id" in self.transcription_result.data:
            transcript_ids = [self.transcription_result.data["id"]]
        elif self.transcript_ids:
            transcript_ids = self.transcript_ids.split(",") or []
            transcript_ids = [t.strip() for t in transcript_ids]

        if not transcript_ids:
            error = "Either a valid Transcription Result or valid Transcript IDs must be provided"
            self.status = error
            return Data(data={"error": error})

        # Get TranscriptGroup and check if there is any error
        transcript_group = aai.TranscriptGroup(transcript_ids=transcript_ids)
        transcript_group, failures = transcript_group.wait_for_completion(return_failures=True)
        if failures:
            error = f"Getting transcriptions failed: {failures[0]}"
            self.status = error
            return Data(data={"error": error})

        for t in transcript_group.transcripts:
            if t.status == aai.TranscriptStatus.error:
                self.status = t.error
                return Data(data={"error": t.error})

        # Perform LeMUR action
        try:
            response = self.perform_lemur_action(transcript_group, self.endpoint)
        except Exception as e:  # noqa: BLE001
            logger.debug("Error running LeMUR", exc_info=True)
            error = f"An Error happened: {e}"
            self.status = error
            return Data(data={"error": error})

        result = Data(data=response)
        self.status = result
        return result

    # 执行具体的 LeMUR 操作（任务/摘要/问答）
    def perform_lemur_action(self, transcript_group: aai.TranscriptGroup, endpoint: str) -> dict:
        logger.info("Endpoint:", endpoint, type(endpoint))
        if endpoint == "task":
            result = transcript_group.lemur.task(
                prompt=self.prompt,
                final_model=self.get_final_model(self.final_model),
                temperature=self.temperature,
                max_output_size=self.max_output_size,
            )
        elif endpoint == "summary":
            result = transcript_group.lemur.summarize(
                final_model=self.get_final_model(self.final_model),
                temperature=self.temperature,
                max_output_size=self.max_output_size,
            )
        elif endpoint == "question-answer":
            questions = self.questions.split(",")
            questions = [aai.LemurQuestion(question=q) for q in questions]
            result = transcript_group.lemur.question(
                questions=questions,
                final_model=self.get_final_model(self.final_model),
                temperature=self.temperature,
                max_output_size=self.max_output_size,
            )
        else:
            msg = f"Endpoint not supported: {endpoint}"
            raise ValueError(msg)

        return result.dict()

    # 将模型名称字符串转换为 AssemblyAI LeMUR 模型枚举值
    def get_final_model(self, model_name: str) -> aai.LemurModel:
        if model_name == "claude3_5_sonnet":
            return aai.LemurModel.claude3_5_sonnet
        if model_name == "claude3_opus":
            return aai.LemurModel.claude3_opus
        if model_name == "claude3_haiku":
            return aai.LemurModel.claude3_haiku
        if model_name == "claude3_sonnet":
            return aai.LemurModel.claude3_sonnet
        msg = f"Model name not supported: {model_name}"
        raise ValueError(msg)
