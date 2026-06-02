from typing import cast

from lfx.custom import Component
from lfx.io import BoolInput, HandleInput, Output, StrInput
from lfx.schema.data import Data


# 通知组件 - 用于向 "Get Notified" 组件生成通知消息
# 通过上下文键存储通知数据，支持追加或覆盖模式
class NotifyComponent(Component):
    # 组件显示名称
    display_name = "Notify"
    # 组件描述：生成通知以供 Get Notified 组件接收
    description = "A component to generate a notification to Get Notified component."
    # 组件图标
    icon = "Notify"
    # 组件内部名称
    name = "Notify"
    # 标记为 Beta 功能
    beta: bool = True

    # 组件输入参数定义
    inputs = [
        # 上下文键：用于标识通知存储位置的键名
        StrInput(
            name="context_key",
            display_name="Context Key",
            info="The key of the context to store the notification.",
            required=True,
        ),
        # 输入数据：支持 Data、JSON、Message、DataFrame、Table 等多种类型
        HandleInput(
            name="input_value",
            display_name="Input Data",
            info="The data to store.",
            required=False,
            input_types=["Data", "JSON", "Message", "DataFrame", "Table"],
        ),
        # 追加模式开关：True 时将数据追加到通知列表，False 时替换已有数据
        BoolInput(
            name="append",
            display_name="Append",
            info="If True, the record will be appended to the notification.",
            value=False,
            required=False,
        ),
    ]

    # 组件输出参数定义
    outputs = [
        # 输出 JSON 格式的处理结果，不使用缓存
        Output(
            display_name="JSON",
            name="result",
            method="notify_components",
            cache=False,
        ),
    ]

    # 异步处理通知的核心方法，将输入数据存储到组件上下文中
    async def notify_components(self) -> Data:
        """Processes and stores a notification in the component's context.

        Normalizes the input value to a `Data` object and stores it under the
        specified context key. If `append` is True, adds the value to a list
        of notifications; otherwise, replaces the existing value. Updates the
        component's status and activates related state vertices in the graph.

        Returns:
            The processed `Data` object stored in the context.

        Raises:
            ValueError: If the component is not part of a graph.
        """
        # 确保组件已绑定到图中，否则无法操作上下文
        if not self._vertex:
            msg = "Notify component must be used in a graph."
            raise ValueError(msg)

        # 获取输入值并标准化为 Data 对象
        input_value: Data | str | dict | None = self.input_value

        # 处理 None 值：创建空的 Data 对象
        if input_value is None:
            input_value = Data(text="")
        elif not isinstance(input_value, Data):
            # 将字符串类型输入转换为 Data 对象
            if isinstance(input_value, str):
                input_value = Data(text=input_value)
            # 将字典类型输入转换为 Data 对象
            elif isinstance(input_value, dict):
                input_value = Data(data=input_value)
            # 其他类型统一转为字符串后再包装为 Data
            else:
                input_value = Data(text=str(input_value))

        # 将标准化后的数据存储到上下文中
        if input_value:
            if self.append:
                # 追加模式：获取当前列表（若不存在则创建），追加新数据
                current_data = self.ctx.get(self.context_key, [])
                if not isinstance(current_data, list):
                    current_data = [current_data]
                current_data.append(input_value)
                self.update_ctx({self.context_key: current_data})
            else:
                # 覆盖模式：直接替换上下文中的数据
                self.update_ctx({self.context_key: input_value})
            # 更新组件状态显示
            self.status = input_value
        else:
            # 无数据时设置默认状态信息
            self.status = "No record provided."

        # 标记当前顶点为状态顶点，并激活图中与该上下文键关联的状态顶点
        self._vertex.is_state = True
        self.graph.activate_state_vertices(name=self.context_key, caller=self._id)

        return cast("Data", input_value)
