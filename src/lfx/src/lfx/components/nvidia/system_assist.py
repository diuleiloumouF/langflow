import asyncio

from lfx.custom.custom_component.component_with_cache import ComponentWithCache
from lfx.io import MessageTextInput, Output
from lfx.schema import Message
from lfx.services.cache.utils import CacheMiss

# Rise 客户端初始化状态的缓存键
RISE_INITIALIZED_KEY = "rise_initialized"


class NvidiaSystemAssistComponent(ComponentWithCache):
    """NVIDIA System-Assist 组件，用于与 NVIDIA GPU 驱动进行交互。

    仅支持 Windows 平台。用户可以通过自然语言查询 GPU 规格、状态，
    并通过 NV-API 执行 GPU 相关操作。
    """

    display_name = "NVIDIA System-Assist"
    description = (
        "(Windows only) Prompts NVIDIA System-Assist to interact with the NVIDIA GPU Driver. "
        "The user may query GPU specifications, state, and ask the NV-API to perform "
        "several GPU-editing acations. The prompt must be human-readable language."
    )
    documentation = "https://docs.langflow.org/bundles-nvidia"
    icon = "NVIDIA"
    # 标记 Rise 客户端是否已初始化
    rise_initialized = False

    # 组件输入：用户提示文本
    inputs = [
        MessageTextInput(
            name="prompt",
            display_name="System-Assist Prompt",
            info="Enter a prompt for NVIDIA System-Assist to process. Example: 'What is my GPU?'",
            value="",
            tool_mode=True,
        ),
    ]

    # 组件输出：System-Assist 的响应
    outputs = [
        Output(display_name="Response", name="response", method="sys_assist_prompt"),
    ]

    def maybe_register_rise_client(self):
        """注册 Rise 客户端（如果尚未注册）。

        通过缓存检查 Rise 客户端是否已初始化，避免重复注册。
        仅支持 Windows 平台，其他平台会抛出 ValueError。
        """
        try:
            from gassist.rise import register_rise_client

            # 检查缓存中 Rise 客户端是否已初始化
            rise_initialized = self._shared_component_cache.get(RISE_INITIALIZED_KEY)
            if not isinstance(rise_initialized, CacheMiss) and rise_initialized:
                return
            self.log("Initializing Rise Client")

            # 注册 Rise 客户端并将初始化状态写入缓存
            register_rise_client()
            self._shared_component_cache.set(key=RISE_INITIALIZED_KEY, value=True)
        except ImportError as e:
            msg = "NVIDIA System-Assist is Windows only and not supported on this platform"
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"An error occurred initializing NVIDIA System-Assist: {e}"
            raise ValueError(msg) from e

    async def sys_assist_prompt(self) -> Message:
        """执行 NVIDIA System-Assist 提示并返回响应消息。

        在线程池中异步调用 Rise 命令，将用户提示发送给
        NVIDIA System-Assist 处理，并将结果包装为 Message 对象返回。
        """
        try:
            from gassist.rise import send_rise_command
        except ImportError as e:
            msg = "NVIDIA System-Assist is Windows only and not supported on this platform"
            raise ValueError(msg) from e

        # 确保 Rise 客户端已注册
        self.maybe_register_rise_client()

        # 在线程池中异步执行 Rise 命令，避免阻塞事件循环
        response = await asyncio.to_thread(send_rise_command, self.prompt)

        # 将响应转换为 Message 对象返回
        return Message(text=response["completed_response"]) if response is not None else Message(text=None)
