from typing import TYPE_CHECKING

from lfx.custom import validate

if TYPE_CHECKING:
    from lfx.custom.custom_component.custom_component import CustomComponent


def eval_custom_component_code(code: str) -> type["CustomComponent"]:
    """Evaluate custom component code.

    评估自定义组件代码，将源代码字符串解析为可实例化的自定义组件类。

    Args:
        code: 自定义组件的 Python 源代码字符串。

    Returns:
        解析并创建的自定义组件类。
    """
    # 从源代码中提取类名
    class_name = validate.extract_class_name(code)
    # 根据类名和源代码动态创建类并返回
    return validate.create_class(code, class_name)
