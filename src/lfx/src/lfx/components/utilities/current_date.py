from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

from lfx.custom.custom_component.component import Component
from lfx.io import DropdownInput, Output
from lfx.log.logger import logger
from lfx.schema.message import Message


# 当前日期组件，返回所选时区的当前日期和时间
class CurrentDateComponent(Component):
    # 组件显示名称
    display_name = "Current Date"
    # 组件描述信息
    description = "Returns the current date and time in the selected timezone."
    # 组件文档链接
    documentation: str = "https://docs.langflow.org/current-date"
    # 组件图标
    icon = "clock"
    # 组件内部名称
    name = "CurrentDate"

    # 组件输入参数定义
    inputs = [
        DropdownInput(
            name="timezone",
            display_name="Timezone",
            options=[],  # 选项通过 update_build_config 动态加载
            value="UTC",
            info="Select the timezone for the current date and time.",
            tool_mode=True,
            real_time_refresh=True,
        ),
    ]

    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):  # noqa: ARG002
        """Dynamically update build config with timezone options."""
        # 动态更新构建配置，添加时区选项
        if field_name == "timezone" or field_name is None:
            build_config["timezone"]["options"] = sorted(tz for tz in available_timezones() if tz != "localtime")
        return build_config

    # 组件输出参数定义
    outputs = [
        Output(display_name="Current Date", name="current_date", method="get_current_date"),
    ]

    # 获取当前日期和时间
    def get_current_date(self) -> Message:
        try:
            tz = ZoneInfo(self.timezone)
            current_date = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
            result = f"Current date and time in {self.timezone}: {current_date}"
            self.status = result
            return Message(text=result)
        except Exception as e:  # noqa: BLE001
            logger.debug("Error getting current date", exc_info=True)
            error_message = f"Error: {e}"
            self.status = error_message
            return Message(text=error_message)
