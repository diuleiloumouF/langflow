# YouTube 搜索组件，通过 YouTube Data API 搜索视频
from contextlib import contextmanager

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import BoolInput, DropdownInput, IntInput, MessageTextInput, SecretStrInput
from lfx.schema.dataframe import DataFrame
from lfx.template.field.base import Output


# YouTube 搜索组件，根据关键词搜索 YouTube 视频并返回结果
class YouTubeSearchComponent(Component):
    """A component that searches YouTube videos."""

    # 组件显示名称
    display_name: str = "YouTube Search"
    # 组件描述
    description: str = "Searches YouTube videos based on query."
    # 组件图标
    icon: str = "YouTube"

    # 组件输入参数定义
    inputs = [
        # 搜索查询关键词
        MessageTextInput(
            name="query",
            display_name="Search Query",
            info="The search query to look for on YouTube.",
            tool_mode=True,
            required=True,
        ),
        # YouTube Data API 密钥
        SecretStrInput(
            name="api_key",
            display_name="YouTube API Key",
            info="Your YouTube Data API key.",
            required=True,
        ),
        # 最大返回结果数
        IntInput(
            name="max_results",
            display_name="Max Results",
            value=10,
            info="The maximum number of results to return.",
        ),
        # 排序方式
        DropdownInput(
            name="order",
            display_name="Sort Order",
            options=["relevance", "date", "rating", "title", "viewCount"],
            value="relevance",
            info="Sort order for the search results.",
        ),
        # 是否包含视频元数据（描述、统计等）
        BoolInput(
            name="include_metadata",
            display_name="Include Metadata",
            value=True,
            info="Include video metadata like description and statistics.",
            advanced=True,
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(name="results", display_name="Search Results", method="search_videos"),
    ]

    # YouTube API 客户端上下文管理器
    @contextmanager
    def youtube_client(self):
        """Context manager for YouTube API client."""
        client = build("youtube", "v3", developerKey=self.api_key)
        try:
            yield client
        finally:
            client.close()

    # 搜索 YouTube 视频并返回 DataFrame
    def search_videos(self) -> DataFrame:
        """Searches YouTube videos and returns results as DataFrame."""
        try:
            with self.youtube_client() as youtube:
                search_response = (
                    youtube.search()
                    .list(
                        q=self.query,
                        part="id,snippet",
                        maxResults=self.max_results,
                        order=self.order,
                        type="video",
                    )
                    .execute()
                )

                results = []
                for search_result in search_response.get("items", []):
                    video_id = search_result["id"]["videoId"]
                    snippet = search_result["snippet"]

                    result = {
                        "video_id": video_id,
                        "title": snippet["title"],
                        "description": snippet["description"],
                        "published_at": snippet["publishedAt"],
                        "channel_title": snippet["channelTitle"],
                        "thumbnail_url": snippet["thumbnails"]["default"]["url"],
                    }

                    if self.include_metadata:
                        # Get video details for additional metadata
                        # 获取视频详情以补充元数据
                        video_response = youtube.videos().list(part="statistics,contentDetails", id=video_id).execute()

                        if video_response.get("items"):
                            video_details = video_response["items"][0]
                            result.update(
                                {
                                    "view_count": int(video_details["statistics"]["viewCount"]),
                                    "like_count": int(video_details["statistics"].get("likeCount", 0)),
                                    "comment_count": int(video_details["statistics"].get("commentCount", 0)),
                                    "duration": video_details["contentDetails"]["duration"],
                                }
                            )

                    results.append(result)

                return DataFrame(pd.DataFrame(results))

        except HttpError as e:
            error_message = f"YouTube API error: {e!s}"
            return DataFrame(pd.DataFrame({"error": [error_message]}))
