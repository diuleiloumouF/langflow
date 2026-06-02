# LangChain 百度千帆聊天模型集成
from langchain_community.chat_models.baidu_qianfan_endpoint import QianfanChatEndpoint

# 模型组件基类、类型定义、输入组件
from lfx.base.models.model import LCModelComponent
from lfx.field_typing.constants import LanguageModel
from lfx.io import DropdownInput, FloatInput, MessageTextInput, SecretStrInput


# 百度千帆聊天模型组件，用于通过百度千帆平台调用大语言模型生成文本
class QianfanChatEndpointComponent(LCModelComponent):
    display_name: str = "Qianfan"
    # 组件描述：使用百度千帆大语言模型生成文本
    description: str = "Generate text using Baidu Qianfan LLMs."
    documentation: str = "https://python.langchain.com/docs/integrations/chat/baidu_qianfan_endpoint"
    icon = "BaiduQianfan"
    name = "BaiduQianfanChatModel"

    # 输入参数定义（继承基础模型输入 + 千帆特有参数）
    inputs = [
        *LCModelComponent.get_base_inputs(),
        # 模型名称选择下拉框，支持多种千帆模型
        DropdownInput(
            name="model",
            display_name="Model Name",
            options=[
                "EB-turbo-AppBuilder",
                "Llama-2-70b-chat",
                "ERNIE-Bot-turbo-AI",
                "ERNIE-Lite-8K-0308",
                "ERNIE-Speed",
                "Qianfan-Chinese-Llama-2-13B",
                "ERNIE-3.5-8K",
                "BLOOMZ-7B",
                "Qianfan-Chinese-Llama-2-7B",
                "XuanYuan-70B-Chat-4bit",
                "AquilaChat-7B",
                "ERNIE-Bot-4",
                "Llama-2-13b-chat",
                "ChatGLM2-6B-32K",
                "ERNIE-Bot",
                "ERNIE-Speed-128k",
                "ERNIE-4.0-8K",
                "Qianfan-BLOOMZ-7B-compressed",
                "ERNIE Speed",
                "Llama-2-7b-chat",
                "Mixtral-8x7B-Instruct",
                "ERNIE 3.5",
                "ERNIE Speed-AppBuilder",
                "ERNIE-Speed-8K",
                "Yi-34B-Chat",
            ],
            info="https://python.langchain.com/docs/integrations/chat/baidu_qianfan_endpoint",
            value="ERNIE-4.0-8K",
        ),
        # 千帆平台 Access Key
        SecretStrInput(
            name="qianfan_ak",
            display_name="Qianfan Ak",
            info="which you could get from  https://cloud.baidu.com/product/wenxinworkshop",
        ),
        # 千帆平台 Secret Key
        SecretStrInput(
            name="qianfan_sk",
            display_name="Qianfan Sk",
            info="which you could get from  https://cloud.baidu.com/product/wenxinworkshop",
        ),
        # Top-p 采样参数（仅 ERNIE-Bot 系列支持）
        FloatInput(
            name="top_p",
            display_name="Top p",
            info="Model params, only supported in ERNIE-Bot and ERNIE-Bot-turbo",
            value=0.8,
            advanced=True,
        ),
        # 温度参数，控制输出随机性
        FloatInput(
            name="temperature",
            display_name="Temperature",
            info="Model params, only supported in ERNIE-Bot and ERNIE-Bot-turbo",
            value=0.95,
        ),
        # 惩罚分数，控制重复内容（仅 ERNIE-Bot 系列支持）
        FloatInput(
            name="penalty_score",
            display_name="Penalty Score",
            info="Model params, only supported in ERNIE-Bot and ERNIE-Bot-turbo",
            value=1.0,
            advanced=True,
        ),
        # 自定义模型端点名称（使用自定义模型时必填）
        MessageTextInput(
            name="endpoint", display_name="Endpoint", info="Endpoint of the Qianfan LLM, required if custom model used."
        ),
    ]

    # 构建并返回百度千帆聊天模型实例
    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        model = self.model
        qianfan_ak = self.qianfan_ak
        qianfan_sk = self.qianfan_sk
        top_p = self.top_p
        temperature = self.temperature
        penalty_score = self.penalty_score
        endpoint = self.endpoint

        try:
            kwargs = {
                "model": model,
                "qianfan_ak": qianfan_ak or None,
                "qianfan_sk": qianfan_sk or None,
                "top_p": top_p,
                "temperature": temperature,
                "penalty_score": penalty_score,
            }

            if endpoint:  # Only add endpoint if it has a value
                kwargs["endpoint"] = endpoint

            output = QianfanChatEndpoint(**kwargs)

        except Exception as e:
            msg = "Could not connect to Baidu Qianfan API."
            raise ValueError(msg) from e

        return output
