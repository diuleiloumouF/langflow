import math

from lfx.log.logger import logger


# 替换数据中无效值（None、null、NaN、NaT）为空字符串或默认值的函数
def replace_none_and_null_with_empty_str(data: list[dict], required_fields: list[str] | None = None) -> list[dict]:
    """Replaces all None, 'null' (case-insensitive), and NaN/NaT float values with empty strings in a list of dicts.

    Args:
        data: List of dictionaries.1
        required_fields: List of field names that must be present in each dictionary.
                        Missing fields will be added with value "Not available".

    Returns:
        List of dictionaries with None, 'null', and NaN/NaT values replaced with "",
        and "NaN", "Infinity", "-Infinity" string values replaced with None.
    """

    # 将单个值中的无效值转换为 "Not available" 字符串
    def convert_value(v):
        if v is None:
            return "Not available"
        if isinstance(v, str):
            v_stripped = v.strip().lower()
            if v_stripped in {"null", "nan", "infinity", "-infinity"}:
                return "Not available"
        if isinstance(v, float):
            try:
                if math.isnan(v):
                    return "Not available"
            except Exception as e:  # noqa: BLE001
                logger.aexception(f"Error converting value {v} to float: {e}")

        if hasattr(v, "isnat") and getattr(v, "isnat", False):
            return "Not available"
        return v

    # 不可用值的占位字符串
    not_avail = "Not available"
    # 将必需字段列表转换为集合，便于快速查找
    required_fields_set = set(required_fields) if required_fields else set()
    # 存储处理后的字典列表
    result = []
    for d in data:
        if not isinstance(d, dict):
            result.append(d)
            continue
        new_dict = {k: convert_value(v) for k, v in d.items()}
        missing = required_fields_set - new_dict.keys()
        if missing:
            for k in missing:
                new_dict[k] = not_avail
        result.append(new_dict)
    return result
