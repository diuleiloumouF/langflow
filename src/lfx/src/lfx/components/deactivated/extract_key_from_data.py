# 自定义组件基类
from lfx.custom.custom_component.custom_component import CustomComponent

# 数据模型
from lfx.schema.data import Data


# 从数据中提取键组件，从 Data 对象中提取指定的键
class ExtractKeyFromDataComponent(CustomComponent):
    display_name = "Extract Key From Data"
    description = "Extracts a key from a data."
    beta: bool = True
    name = "ExtractKeyFromData"

    # 字段配置
    field_config = {
        "data": {"display_name": "Data"},
        "keys": {
            "display_name": "Keys",
            "info": "The keys to extract from the data.",
            "input_types": [],
        },
        "silent_error": {
            "display_name": "Silent Errors",
            "info": "If True, errors will not be raised.",
            "advanced": True,
        },
    }

    # 构建方法：从数据中提取指定的键
    def build(self, data: Data, keys: list[str], *, silent_error: bool = True) -> Data:
        """Extracts the keys from a data.

        Args:
            data (Data): The data from which to extract the keys.
            keys (list[str]): The keys to extract from the data.
            silent_error (bool): If True, errors will not be raised.

        Returns:
            dict: The extracted keys.
        """
        extracted_keys = {}
        for key in keys:
            try:
                extracted_keys[key] = getattr(data, key)
            except AttributeError as e:
                # 如果不静默错误，则抛出异常
                if not silent_error:
                    msg = f"The key '{key}' does not exist in the data."
                    raise KeyError(msg) from e
        # 将提取的键值对包装为 Data 对象
        return_data = Data(data=extracted_keys)
        self.status = return_data
        return return_data
