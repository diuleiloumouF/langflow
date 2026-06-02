# 导入组件基类
from lfx.custom import Component

# 导入输入输出类型
from lfx.io import Output, StrInput

# 导入 Data 数据类型
from lfx.schema.data import Data


class ListenComponent(Component):
    # 监听组件：用于监听流中的通知或数据事件
    display_name = "Listen"  # 组件在画布上显示的名称
    description = "A component to listen for a notification."  # 组件描述信息
    name = "Listen"  # 组件唯一标识名
    beta: bool = True  # 标记为 beta 版本的功能
    icon = "Radio"  # 组件图标

    # 组件输入参数定义
    inputs = [
        StrInput(
            name="context_key",
            display_name="Context Key",
            info="The key of the context to listen for.",  # 要监听的上下文键
            input_types=["Message"],  # 支持的消息类型
            required=True,  # 必填参数
        )
    ]

    # 组件输出定义：输出 JSON 格式的数据
    outputs = [Output(name="data", display_name="JSON", method="listen_for_data", cache=False)]

    def listen_for_data(self) -> Data:
        """Retrieves a Data object from the component context using the provided context key.

        If the specified context key does not exist in the context, returns an empty Data object.
        """
        # 从组件上下文中获取指定键的数据，若不存在则返回空 Data 对象
        return self.ctx.get(self.context_key, Data(text=""))
