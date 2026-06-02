# 操作系统接口，用于访问环境变量
import os

# 组件基类
from lfx.custom.custom_component.component import Component

# 输入组件类型
from lfx.inputs.inputs import StrInput

# 消息模型
from lfx.schema.message import Message

# 输出字段定义
from lfx.template.field.base import Output


# 获取环境变量组件，从系统中获取指定环境变量的值
class GetEnvVar(Component):
    display_name = "Get Environment Variable"
    description = "Gets the value of an environment variable from the system."
    icon = "AstraDB"
    legacy = True

    # 输入参数定义
    inputs = [
        # 环境变量名称
        StrInput(
            name="env_var_name",
            display_name="Environment Variable Name",
            info="Name of the environment variable to get",
        )
    ]

    # 输出参数定义
    outputs = [
        Output(display_name="Environment Variable Value", name="env_var_value", method="process_inputs"),
    ]

    # 处理输入：获取环境变量的值
    def process_inputs(self) -> Message:
        # 检查环境变量是否存在
        if self.env_var_name not in os.environ:
            msg = f"Environment variable {self.env_var_name} not set"
            raise ValueError(msg)
        return Message(text=os.environ[self.env_var_name])
