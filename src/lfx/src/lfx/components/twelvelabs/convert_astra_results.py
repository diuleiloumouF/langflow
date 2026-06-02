from typing import Any

from lfx.custom import Component
from lfx.io import HandleInput, Output
from lfx.schema import Data
from lfx.schema.message import Message


class ConvertAstraToTwelveLabs(Component):
    """Convert Astra DB search results to TwelveLabs Pegasus inputs."""

    # 组件显示名称，在画布上展示给用户
    display_name = "Convert Astra DB to Pegasus Input"
    # 组件描述信息，说明组件的功能
    description = "Converts Astra DB search results to inputs compatible with TwelveLabs Pegasus."
    # 组件图标
    icon = "TwelveLabs"
    # 组件内部名称，用于代码引用
    name = "ConvertAstraToTwelveLabs"
    # 组件文档链接
    documentation = "https://github.com/twelvelabs-io/twelvelabs-developer-experience/blob/main/integrations/Langflow/TWELVE_LABS_COMPONENTS_README.md"

    # 输入参数定义：接收 Astra DB 的搜索结果
    inputs = [
        HandleInput(
            name="astra_results",
            display_name="Astra DB Results",
            input_types=["Data", "JSON"],
            info="Search results from Astra DB component",
            required=True,
            is_list=True,
        )
    ]

    # 输出参数定义：提取出的索引ID和视频ID，分别作为消息输出
    outputs = [
        Output(
            name="index_id",
            display_name="Index ID",
            type_=Message,
            method="get_index_id",
        ),
        Output(
            name="video_id",
            display_name="Video ID",
            type_=Message,
            method="get_video_id",
        ),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 存储提取到的视频ID
        self._video_id = None
        # 存储提取到的索引ID
        self._index_id = None

    def build(self, **kwargs: Any) -> None:  # noqa: ARG002 - Required for parent class compatibility
        """Process the Astra DB results and extract TwelveLabs index information."""
        # 如果没有输入结果，直接返回
        if not self.astra_results:
            return

        # 将单个结果转换为列表，统一处理逻辑
        results = self.astra_results if isinstance(self.astra_results, list) else [self.astra_results]

        # 遍历搜索结果，尝试从元数据中提取索引信息
        for doc in results:
            # 跳过非 Data 类型的文档
            if not isinstance(doc, Data):
                continue

            # 获取元数据，处理可能的嵌套结构
            metadata = {}
            if hasattr(doc, "metadata") and isinstance(doc.metadata, dict):
                # 使用 .get() 方法处理嵌套的元数据结构
                metadata = doc.metadata.get("metadata", doc.metadata)

            # 从元数据中提取 index_id 和 video_id
            self._index_id = metadata.get("index_id")
            self._video_id = metadata.get("video_id")

            # 如果已经找到两个值，可以停止搜索
            if self._index_id and self._video_id:
                break

    def get_video_id(self) -> Message:
        """Return the extracted video ID as a Message."""
        # 调用 build 方法确保数据已处理
        self.build()
        # 将视频ID封装为消息返回，如果为空则返回空字符串
        return Message(text=self._video_id if self._video_id else "")

    def get_index_id(self) -> Message:
        """Return the extracted index ID as a Message."""
        # 调用 build 方法确保数据已处理
        self.build()
        # 将索引ID封装为消息返回，如果为空则返回空字符串
        return Message(text=self._index_id if self._index_id else "")
