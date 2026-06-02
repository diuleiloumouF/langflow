import json

import httpx

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output
from lfx.log.logger import logger
from lfx.schema.data import Data


# Olivya 电话外呼组件，用于通过 Olivya 平台发起外呼请求
class OlivyaComponent(Component):
    display_name = "Place Call"
    description = "A component to create an outbound call request from Olivya's platform."
    documentation: str = "https://docs.olivya.io"
    icon = "Olivya"
    name = "OlivyaComponent"

    # 组件输入参数定义
    inputs = [
        MessageTextInput(
            name="api_key",
            display_name="Olivya API Key",
            info="Your API key for authentication",
            value="",
            required=True,
        ),
        MessageTextInput(
            name="from_number",
            display_name="From Number",
            info="The Agent's phone number",
            value="",
            required=True,
        ),
        MessageTextInput(
            name="to_number",
            display_name="To Number",
            info="The recipient's phone number",
            value="",
            required=True,
        ),
        MessageTextInput(
            name="first_message",
            display_name="First Message",
            info="The Agent's introductory message",
            value="",
            required=False,
            tool_mode=True,
        ),
        MessageTextInput(
            name="system_prompt",
            display_name="System Prompt",
            info="The system prompt to guide the interaction",
            value="",
            required=False,
        ),
        MessageTextInput(
            name="conversation_history",
            display_name="Conversation History",
            info="The summary of the conversation",
            value="",
            required=False,
            tool_mode=True,
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(display_name="Output", name="output", method="build_output"),
    ]

    # 构建输出结果，向 Olivya 平台发送外呼请求并返回响应数据
    async def build_output(self) -> Data:
        try:
            # 构造请求载荷，包含变量参数和来电/去电号码
            payload = {
                "variables": {
                    "first_message": self.first_message.strip() if self.first_message else None,
                    "system_prompt": self.system_prompt.strip() if self.system_prompt else None,
                    "conversation_history": self.conversation_history.strip() if self.conversation_history else None,
                },
                "from_number": self.from_number.strip(),
                "to_number": self.to_number.strip(),
            }

            # 构造请求头，包含 API 认证信息
            headers = {
                "Authorization": self.api_key.strip(),
                "Content-Type": "application/json",
            }

            await logger.ainfo("Sending POST request with payload: %s", payload)

            # 使用异步 HTTP 客户端发送 POST 请求，超时时间为 10 秒
            # Send the POST request with a timeout
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://phone.olivya.io/create_zap_call",
                    headers=headers,
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()

                # 解析并返回成功的响应数据
                # Parse and return the successful response
                response_data = response.json()
                await logger.ainfo("Request successful: %s", response_data)

        # 捕获 HTTP 状态码错误（如 4xx、5xx）
        except httpx.HTTPStatusError as http_err:
            await logger.aexception("HTTP error occurred")
            response_data = {"error": f"HTTP error occurred: {http_err}", "response_text": response.text}
        # 捕获网络请求层面的错误（如连接超时、DNS 解析失败等）
        except httpx.RequestError as req_err:
            await logger.aexception("Request failed")
            response_data = {"error": f"Request failed: {req_err}"}
        # 捕获 JSON 解析错误（响应体不是合法的 JSON）
        except json.JSONDecodeError as json_err:
            await logger.aexception("Response parsing failed")
            response_data = {"error": f"Response parsing failed: {json_err}", "raw_response": response.text}
        except Exception as e:  # noqa: BLE001
            await logger.aexception("An unexpected error occurred")
            response_data = {"error": f"An unexpected error occurred: {e!s}"}

        # 将响应数据封装为 Data 对象返回
        # Return the response as part of the output
        return Data(value=response_data)
