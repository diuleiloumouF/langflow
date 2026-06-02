from __future__ import annotations

from typing import TYPE_CHECKING, Any

# 导入动态模块加载工具函数
from lfx.components._importing import import_mod

# 仅在类型检查时导入各组件类，避免运行时加载不必要的依赖
if TYPE_CHECKING:
    # Astra DB 查询结果转 TwelveLabs 格式的组件
    from .convert_astra_results import ConvertAstraToTwelveLabs

    # Pegasus 索引视频组件，用于将视频添加到索引
    from .pegasus_index import PegasusIndexVideo

    # 视频分割组件，用于将长视频拆分为多个片段
    from .split_video import SplitVideoComponent

    # TwelveLabs 文本嵌入组件，用于生成文本向量
    from .text_embeddings import TwelveLabsTextEmbeddingsComponent

    # TwelveLabs Pegasus 多模态模型交互组件
    from .twelvelabs_pegasus import TwelveLabsPegasus

    # TwelveLabs 视频嵌入组件，用于生成视频向量
    from .video_embeddings import TwelveLabsVideoEmbeddingsComponent

    # 视频文件处理组件，用于加载和处理视频文件
    from .video_file import VideoFileComponent

# 动态导入映射表：组件类名 -> 所在模块名
_dynamic_imports = {
    "ConvertAstraToTwelveLabs": "convert_astra_results",
    "PegasusIndexVideo": "pegasus_index",
    "SplitVideoComponent": "split_video",
    "TwelveLabsPegasus": "twelvelabs_pegasus",
    "TwelveLabsTextEmbeddingsComponent": "text_embeddings",
    "TwelveLabsVideoEmbeddingsComponent": "video_embeddings",
    "VideoFileComponent": "video_file",
}

# 模块公开导出的组件列表
__all__ = [
    "ConvertAstraToTwelveLabs",
    "PegasusIndexVideo",
    "SplitVideoComponent",
    "TwelveLabsPegasus",
    "TwelveLabsTextEmbeddingsComponent",
    "TwelveLabsVideoEmbeddingsComponent",
    "VideoFileComponent",
]


def __getattr__(attr_name: str) -> Any:
    """Lazily import twelvelabs components on attribute access."""
    # 属性名不在映射表中时，抛出 AttributeError
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        # 通过动态导入机制按需加载对应组件模块
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    # 将成功导入的组件缓存到全局命名空间，避免重复导入
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    # 限制 dir() 输出仅为模块公开导出的组件列表
    return list(__all__)
