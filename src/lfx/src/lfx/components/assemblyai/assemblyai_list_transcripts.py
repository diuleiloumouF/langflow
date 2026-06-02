# AssemblyAI SDK
import assemblyai as aai

# 组件基类、输入/输出定义、日志、数据模型
from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, DropdownInput, IntInput, MessageTextInput, Output, SecretStrInput
from lfx.log.logger import logger
from lfx.schema.data import Data


# AssemblyAI 转录列表组件，用于检索 AssemblyAI 中的转录记录并支持筛选
class AssemblyAIListTranscripts(Component):
    display_name = "AssemblyAI List Transcripts"
    # 组件描述：从 AssemblyAI 检索转录列表，支持筛选选项
    description = "Retrieve a list of transcripts from AssemblyAI with filtering options"
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
        # 最大返回转录数量
        IntInput(
            name="limit",
            display_name="Limit",
            info="Maximum number of transcripts to retrieve (default: 20, use 0 for all)",
            value=20,
        ),
        # 按状态筛选：全部/排队中/处理中/已完成/错误
        DropdownInput(
            name="status_filter",
            display_name="Status Filter",
            options=["all", "queued", "processing", "completed", "error"],
            value="all",
            info="Filter by transcript status",
            advanced=True,
        ),
        # 按创建日期筛选（YYYY-MM-DD 格式）
        MessageTextInput(
            name="created_on",
            display_name="Created On",
            info="Only get transcripts created on this date (YYYY-MM-DD)",
            advanced=True,
        ),
        # 仅获取被限流的转录记录
        BoolInput(
            name="throttled_only",
            display_name="Throttled Only",
            info="Only get throttled transcripts, overrides the status filter",
            advanced=True,
        ),
    ]

    # 输出参数：转录列表
    outputs = [
        Output(display_name="Transcript List", name="transcript_list", method="list_transcripts"),
    ]

    # 列出转录记录
    def list_transcripts(self) -> list[Data]:
        aai.settings.api_key = self.api_key

        params = aai.ListTranscriptParameters()
        if self.limit:
            params.limit = self.limit
        if self.status_filter != "all":
            params.status = self.status_filter
        if self.created_on and self.created_on.text:
            params.created_on = self.created_on.text
        if self.throttled_only:
            params.throttled_only = True

        try:
            transcriber = aai.Transcriber()

            def convert_page_to_data_list(page):
                return [Data(**t.dict()) for t in page.transcripts]

            if self.limit == 0:
                # paginate over all pages
                params.limit = 100
                page = transcriber.list_transcripts(params)
                transcripts = convert_page_to_data_list(page)

                while page.page_details.before_id_of_prev_url is not None:
                    params.before_id = page.page_details.before_id_of_prev_url
                    page = transcriber.list_transcripts(params)
                    transcripts.extend(convert_page_to_data_list(page))
            else:
                # just one page
                page = transcriber.list_transcripts(params)
                transcripts = convert_page_to_data_list(page)

        except Exception as e:  # noqa: BLE001
            logger.debug("Error listing transcripts", exc_info=True)
            error_data = Data(data={"error": f"An error occurred: {e}"})
            self.status = [error_data]
            return [error_data]

        self.status = transcripts
        return transcripts
