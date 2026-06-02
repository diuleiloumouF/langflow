# IO 模块，用于创建内存文件对象
import io

# python-dotenv 库，用于加载 .env 文件
from dotenv import load_dotenv

# 组件基类
from lfx.custom.custom_component.component import Component

# 多行密钥输入组件
from lfx.inputs.inputs import MultilineSecretInput

# 消息模型
from lfx.schema.message import Message

# 输出字段定义
from lfx.template.field.base import Output


# Dotenv 组件，将 .env 文件内容加载到环境变量中
class Dotenv(Component):
    display_name = "Dotenv"
    description = "Load .env file into env vars"
    icon = "AstraDB"
    legacy = True

    # 输入参数定义
    inputs = [
        # .env 文件内容（敏感信息，建议使用密码类型的全局变量）
        MultilineSecretInput(
            name="dotenv_file_content",
            display_name="Dotenv file content",
            info="Paste the content of your .env file directly, since contents are sensitive, "
            "using a Global variable set as 'password' is recommended",
        )
    ]

    # 输出参数定义
    outputs = [
        Output(display_name="env_set", name="env_set", method="process_inputs"),
    ]

    # 处理输入：将 .env 文件内容加载到环境变量
    def process_inputs(self) -> Message:
        # 将字符串内容转换为文件对象
        fake_file = io.StringIO(self.dotenv_file_content)
        result = load_dotenv(stream=fake_file, override=True)

        message = Message(text="No variables found in .env")
        if result:
            message = Message(text="Loaded .env")
        return message
