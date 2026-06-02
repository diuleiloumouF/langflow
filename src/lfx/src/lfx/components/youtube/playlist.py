# YouTube 播放列表组件，从 YouTube 播放列表中提取所有视频 URL
from pytube import Playlist  # Ensure you have pytube installed

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import MessageTextInput
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.template.field.base import Output


# YouTube 播放列表组件，提取播放列表中的所有视频链接
class YouTubePlaylistComponent(Component):
    # 组件显示名称
    display_name = "YouTube Playlist"
    # 组件描述
    description = "Extracts all video URLs from a YouTube playlist."
    # 组件图标
    icon = "YouTube"  # Replace with a suitable icon

    # 组件输入参数定义
    inputs = [
        # YouTube 播放列表 URL
        MessageTextInput(
            name="playlist_url",
            display_name="Playlist URL",
            info="URL of the YouTube playlist.",
            required=True,
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(display_name="Video URLs", name="video_urls", method="extract_video_urls"),
    ]

    # 提取播放列表中的所有视频 URL 并返回 DataFrame
    def extract_video_urls(self) -> DataFrame:
        playlist_url = self.playlist_url
        playlist = Playlist(playlist_url)
        video_urls = [video.watch_url for video in playlist.videos]

        return DataFrame([Data(data={"video_url": url}) for url in video_urls])
