# from lfx.field_typing import Data
# 从 lfx 模块导入 Component 基类，用于创建自定义组件
from lfx.custom.custom_component.component import Component

# 导入输入和输出定义工具
from lfx.io import MessageTextInput, Output

# 导入 Data 数据类型，用于组件间的数据传递
from lfx.schema.data import Data


# 自定义组件类，继承自 Component 基类
# 该类作为模板，展示如何创建自定义的 Langflow 组件
class CustomComponent(Component):
    # 组件在 Langflow 画布上显示的名称
    display_name = "Custom Component"
    # 组件的描述信息，帮助用户理解组件用途
    description = "Use as a template to create your own component."
    # 组件文档链接，指向组件的官方文档页面
    documentation: str = "https://docs.langflow.org/components-custom-components"
    # 组件图标名称，用于在画布上显示图标
    icon = "code"
    # 组件的内部唯一标识名称
    name = "CustomComponent"

    # 组件的输入参数列表
    inputs = [
        # 消息文本输入，用于接收用户输入的文本值
        MessageTextInput(
            name="input_value",
            display_name="Input Value",
            info="This is a custom component Input",
            value="Hello, World!",  # 默认值
            tool_mode=True,  # 启用工具模式
        ),
    ]

    # 组件的输出列表
    outputs = [
        # 定义一个名为 "output" 的输出，通过 build_output 方法构建
        Output(display_name="Output", name="output", method="build_output"),
    ]

    # 构建组件输出的方法，将输入值包装为 Data 对象返回
    def build_output(self) -> Data:
        # 创建 Data 对象，将输入值作为其内容
        data = Data(value=self.input_value)
        # 将数据设置为组件状态，用于在画布上显示
        self.status = data
        return data
