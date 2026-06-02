# YouTube 评论组件，通过 YouTube Data API 获取和分析视频评论
from contextlib import contextmanager

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import BoolInput, DropdownInput, IntInput, MessageTextInput, SecretStrInput
from lfx.schema.dataframe import DataFrame
from lfx.template.field.base import Output


# YouTube 评论组件，获取视频评论并返回结构化 DataFrame
class YouTubeCommentsComponent(Component):
    """A component that retrieves comments from YouTube videos."""

    # 组件显示名称
    display_name: str = "YouTube Comments"
    # 组件描述
    description: str = "Retrieves and analyzes comments from YouTube videos."
    # 组件图标
    icon: str = "YouTube"

    # Constants
    # 评论被禁用的状态码
    COMMENTS_DISABLED_STATUS = 403
    # 视频未找到状态码
    NOT_FOUND_STATUS = 404
    # API 单次最大返回结果数
    API_MAX_RESULTS = 100

    # 组件输入参数定义
    inputs = [
        # YouTube 视频 URL
        MessageTextInput(
            name="video_url",
            display_name="Video URL",
            info="The URL of the YouTube video to get comments from.",
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
        # 最大返回评论数
        IntInput(
            name="max_results",
            display_name="Max Results",
            value=20,
            info="The maximum number of comments to return.",
        ),
        # 排序方式：按时间或相关性
        DropdownInput(
            name="sort_by",
            display_name="Sort By",
            options=["time", "relevance"],
            value="relevance",
            info="Sort comments by time or relevance.",
        ),
        # 是否包含回复评论
        BoolInput(
            name="include_replies",
            display_name="Include Replies",
            value=False,
            info="Whether to include replies to comments.",
            advanced=True,
        ),
        # 是否包含指标数据（点赞数、回复数）
        BoolInput(
            name="include_metrics",
            display_name="Include Metrics",
            value=True,
            info="Include metrics like like count and reply count.",
            advanced=True,
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(name="comments", display_name="Comments", method="get_video_comments"),
    ]

    # 从 YouTube URL 中提取视频 ID
    def _extract_video_id(self, video_url: str) -> str:
        """Extracts the video ID from a YouTube URL."""
        import re

        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu.be\/|youtube.com\/embed\/)([^&\n?#]+)",
            r"youtube.com\/shorts\/([^&\n?#]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)

        return video_url.strip()

    # 处理单条回复评论
    def _process_reply(self, reply: dict, parent_id: str, *, include_metrics: bool = True) -> dict:
        """Process a single reply comment."""
        reply_snippet = reply["snippet"]
        reply_data = {
            "comment_id": reply["id"],
            "parent_comment_id": parent_id,
            "author": reply_snippet["authorDisplayName"],
            "text": reply_snippet["textDisplay"],
            "published_at": reply_snippet["publishedAt"],
            "is_reply": True,
        }
        if include_metrics:
            reply_data["like_count"] = reply_snippet["likeCount"]
            reply_data["reply_count"] = 0  # Replies can't have replies

        return reply_data

    # 处理单条评论线程（包含顶级评论及其回复）
    def _process_comment(
        self, item: dict, *, include_metrics: bool = True, include_replies: bool = False
    ) -> list[dict]:
        """Process a single comment thread."""
        comment = item["snippet"]["topLevelComment"]["snippet"]
        comment_id = item["snippet"]["topLevelComment"]["id"]

        # Basic comment data
        # 构建基本评论数据
        processed_comments = [
            {
                "comment_id": comment_id,
                "parent_comment_id": "",  # Empty for top-level comments
                "author": comment["authorDisplayName"],
                "author_channel_url": comment.get("authorChannelUrl", ""),
                "text": comment["textDisplay"],
                "published_at": comment["publishedAt"],
                "updated_at": comment["updatedAt"],
                "is_reply": False,
            }
        ]

        # Add metrics if requested
        # 添加指标数据（如果请求了）
        if include_metrics:
            processed_comments[0].update(
                {
                    "like_count": comment["likeCount"],
                    "reply_count": item["snippet"]["totalReplyCount"],
                }
            )

        # Add replies if requested
        # 添加回复评论（如果请求了且存在回复）
        if include_replies and item["snippet"]["totalReplyCount"] > 0 and "replies" in item:
            for reply in item["replies"]["comments"]:
                reply_data = self._process_reply(reply, parent_id=comment_id, include_metrics=include_metrics)
                processed_comments.append(reply_data)

        return processed_comments

    # YouTube API 客户端上下文管理器
    @contextmanager
    def youtube_client(self):
        """Context manager for YouTube API client."""
        client = build("youtube", "v3", developerKey=self.api_key)
        try:
            yield client
        finally:
            client.close()

    # 获取视频评论并返回 DataFrame
    def get_video_comments(self) -> DataFrame:
        """Retrieves comments from a YouTube video and returns as DataFrame."""
        try:
            # Extract video ID from URL
            video_id = self._extract_video_id(self.video_url)

            # Use context manager for YouTube API client
            with self.youtube_client() as youtube:
                comments_data = []
                results_count = 0
                request = youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=min(self.API_MAX_RESULTS, self.max_results),
                    order=self.sort_by,
                    textFormat="plainText",
                )

                while request and results_count < self.max_results:
                    response = request.execute()

                    for item in response.get("items", []):
                        if results_count >= self.max_results:
                            break

                        comments = self._process_comment(
                            item, include_metrics=self.include_metrics, include_replies=self.include_replies
                        )
                        comments_data.extend(comments)
                        results_count += 1

                    # Get the next page if available and needed
                    # 获取下一页数据（如果需要）
                    if "nextPageToken" in response and results_count < self.max_results:
                        request = youtube.commentThreads().list(
                            part="snippet,replies",
                            videoId=video_id,
                            maxResults=min(self.API_MAX_RESULTS, self.max_results - results_count),
                            order=self.sort_by,
                            textFormat="plainText",
                            pageToken=response["nextPageToken"],
                        )
                    else:
                        request = None

                # Convert to DataFrame
                comments_df = pd.DataFrame(comments_data)

                # Add video metadata
                comments_df["video_id"] = video_id
                comments_df["video_url"] = self.video_url

                # Sort columns for better organization
                # 整理列顺序
                column_order = [
                    "video_id",
                    "video_url",
                    "comment_id",
                    "parent_comment_id",
                    "is_reply",
                    "author",
                    "author_channel_url",
                    "text",
                    "published_at",
                    "updated_at",
                ]

                if self.include_metrics:
                    column_order.extend(["like_count", "reply_count"])

                comments_df = comments_df[column_order]

                return DataFrame(comments_df)

        except HttpError as e:
            error_message = f"YouTube API error: {e!s}"
            if e.resp.status == self.COMMENTS_DISABLED_STATUS:
                error_message = "Comments are disabled for this video or API quota exceeded."
            elif e.resp.status == self.NOT_FOUND_STATUS:
                error_message = "Video not found."

            return DataFrame(pd.DataFrame({"error": [error_message]}))
