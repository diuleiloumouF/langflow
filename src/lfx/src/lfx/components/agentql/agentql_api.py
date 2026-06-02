import httpx

from lfx.custom.custom_component.component import Component
from lfx.field_typing.range_spec import RangeSpec
from lfx.io import BoolInput, DropdownInput, IntInput, MessageTextInput, MultilineInput, Output, SecretStrInput
from lfx.log.logger import logger
from lfx.schema.data import Data


# AgentQL 网页数据提取组件，通过 AgentQL API 从网页中提取结构化数据
class AgentQL(Component):
    display_name = "Extract Web Data"
    description = "Extracts structured data from a web page using an AgentQL query or a Natural Language description."
    documentation: str = "https://docs.agentql.com/rest-api/api-reference"
    icon = "AgentQL"
    name = "AgentQL"

    # 组件输入参数定义
    inputs = [
        # API 密钥，用于身份验证
        SecretStrInput(
            name="api_key",
            display_name="AgentQL API Key",
            required=True,
            password=True,
            info="Your AgentQL API key from dev.agentql.com",
        ),
        # 目标网页 URL
        MessageTextInput(
            name="url",
            display_name="URL",
            required=True,
            info="The URL of the public web page you want to extract data from.",
            tool_mode=True,
        ),
        # AgentQL 查询语句（与 Prompt 二选一）
        MultilineInput(
            name="query",
            display_name="AgentQL Query",
            required=False,
            info="The AgentQL query to execute. Learn more at https://docs.agentql.com/agentql-query or use a prompt.",
            tool_mode=True,
        ),
        # 自然语言提示词，作为 AgentQL 查询的替代方式
        MultilineInput(
            name="prompt",
            display_name="Prompt",
            required=False,
            info="A Natural Language description of the data to extract from the page. Alternative to AgentQL query.",
            tool_mode=True,
        ),
        # 隐身模式开关，用于实验性反机器人规避策略
        BoolInput(
            name="is_stealth_mode_enabled",
            display_name="Enable Stealth Mode (Beta)",
            info="Enable experimental anti-bot evasion strategies. May not work for all websites at all times.",
            value=False,
            advanced=True,
        ),
        # 请求超时时间（秒）
        IntInput(
            name="timeout",
            display_name="Timeout",
            info="Seconds to wait for a request.",
            value=900,
            advanced=True,
        ),
        # 请求模式：标准模式（深度分析）或快速模式
        DropdownInput(
            name="mode",
            display_name="Request Mode",
            info="'standard' uses deep data analysis, while 'fast' trades some depth of analysis for speed.",
            options=["fast", "standard"],
            value="fast",
            advanced=True,
        ),
        # 页面加载等待时间（秒）
        IntInput(
            name="wait_for",
            display_name="Wait For",
            info="Seconds to wait for the page to load before extracting data.",
            value=0,
            range_spec=RangeSpec(min=0, max=10, step_type="int"),
            advanced=True,
        ),
        # 是否在提取数据前滚动到页面底部
        BoolInput(
            name="is_scroll_to_bottom_enabled",
            display_name="Enable scroll to bottom",
            info="Scroll to bottom of the page before extracting data.",
            value=False,
            advanced=True,
        ),
        # 是否在提取数据前截取页面截图
        BoolInput(
            name="is_screenshot_enabled",
            display_name="Enable screenshot",
            info="Take a screenshot before extracting data. Returned in 'metadata' as a Base64 string.",
            value=False,
            advanced=True,
        ),
    ]

    # 组件输出定义，返回 JSON 格式的数据
    outputs = [
        Output(display_name="JSON", name="data", method="build_output"),
    ]

    # 构建输出数据：调用 AgentQL API 提取网页结构化数据
    def build_output(self) -> Data:
        # AgentQL 数据查询 API 端点
        endpoint = "https://api.agentql.com/v1/query-data"
        # 请求头，包含 API 密钥和内容类型
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "X-TF-Request-Origin": "langflow",
        }

        # 构建请求载荷
        payload = {
            "url": self.url,
            "query": self.query,
            "prompt": self.prompt,
            "params": {
                "mode": self.mode,
                "wait_for": self.wait_for,
                "is_scroll_to_bottom_enabled": self.is_scroll_to_bottom_enabled,
                "is_screenshot_enabled": self.is_screenshot_enabled,
            },
            "metadata": {
                "experimental_stealth_mode_enabled": self.is_stealth_mode_enabled,
            },
        }

        # 参数校验：query 和 prompt 必须且只能提供其一
        if not self.prompt and not self.query:
            self.status = "Either Query or Prompt must be provided."
            raise ValueError(self.status)
        if self.prompt and self.query:
            self.status = "Both Query and Prompt can't be provided at the same time."
            raise ValueError(self.status)

        try:
            # 发送 POST 请求到 AgentQL API
            response = httpx.post(endpoint, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()

            # 解析响应 JSON 数据
            json = response.json()
            data = Data(result=json["data"], metadata=json["metadata"])

        except httpx.HTTPStatusError as e:
            response = e.response
            # 处理 401 未授权错误（API 密钥无效）
            if response.status_code == httpx.codes.UNAUTHORIZED:
                self.status = "Please, provide a valid API Key. You can create one at https://dev.agentql.com."
            else:
                try:
                    error_json = response.json()
                    logger.error(
                        f"Failure response: '{response.status_code} {response.reason_phrase}' with body: {error_json}"
                    )
                    msg = error_json["error_info"] if "error_info" in error_json else error_json["detail"]
                except (ValueError, TypeError):
                    msg = f"HTTP {e}."
                self.status = msg
            raise ValueError(self.status) from e

        else:
            # 请求成功，设置状态并返回数据
            self.status = data
            return data
