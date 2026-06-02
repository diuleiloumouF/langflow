"""Git 文档加载器组件。

提供从本地或远程 Git 仓库加载和过滤文档的功能。
支持按文件路径模式和文件内容正则表达式进行过滤。
"""

import re
import tempfile
from contextlib import asynccontextmanager
from fnmatch import fnmatch
from pathlib import Path

import anyio
from langchain_community.document_loaders.git import GitLoader

from lfx.custom.custom_component.component import Component
from lfx.io import DropdownInput, MessageTextInput, Output
from lfx.schema.data import Data


# Git 文档加载器组件：从本地或远程 Git 仓库加载文档
class GitLoaderComponent(Component):
    # 组件显示名称
    display_name = "Git"
    # 组件描述信息
    description = (
        "Load and filter documents from a local or remote Git repository. "
        "Use a local repo path or clone from a remote URL."
    )
    # 追踪类型，用于工具追踪
    trace_type = "tool"
    # 组件图标
    icon = "GitLoader"

    # 组件输入参数定义
    inputs = [
        # 仓库来源选择：本地路径或远程 URL
        DropdownInput(
            name="repo_source",
            display_name="Local Repository Path",
            options=["Local", "Remote"],
            required=True,
            info="Select whether to use a local repo path or clone from a remote URL.",
            real_time_refresh=True,
        ),
        # 本地仓库路径输入（仅本地模式显示）
        MessageTextInput(
            name="repo_path",
            display_name="Local Repository Path",
            required=False,
            info="The local path to the existing Git repository (used if 'Local' is selected).",
            dynamic=True,
            show=False,
        ),
        # 远程仓库克隆 URL 输入（仅远程模式显示）
        MessageTextInput(
            name="clone_url",
            display_name="Clone URL",
            required=False,
            info="The URL of the Git repository to clone (used if 'Clone' is selected).",
            dynamic=True,
            show=False,
        ),
        # 分支名称，默认为 main
        MessageTextInput(
            name="branch",
            display_name="Branch",
            required=False,
            value="main",
            info="The branch to load files from. Defaults to 'main'.",
        ),
        # 文件路径过滤模式（高级选项）
        MessageTextInput(
            name="file_filter",
            display_name="File Filter",
            required=False,
            advanced=True,
            info=(
                "Patterns to filter files. For example:\n"
                "Include only .py files: '*.py'\n"
                "Exclude .py files: '!*.py'\n"
                "Multiple patterns can be separated by commas."
            ),
        ),
        # 内容过滤正则表达式（高级选项）
        MessageTextInput(
            name="content_filter",
            display_name="Content Filter",
            required=False,
            advanced=True,
            info="A regex pattern to filter files based on their content.",
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(name="data", display_name="JSON", method="load_documents"),
    ]

    # 静态方法：判断文件是否为二进制文件
    @staticmethod
    def is_binary(file_path: str | Path) -> bool:
        """Check if a file is binary by looking for null bytes."""
        # 通过检测空字节判断文件是否为二进制
        try:
            with Path(file_path).open("rb") as file:
                content = file.read(1024)
                return b"\x00" in content
        except Exception:  # noqa: BLE001
            # 读取异常时视为二进制文件
            return True

    # 静态方法：检查文件路径是否匹配给定的 glob 模式
    @staticmethod
    def check_file_patterns(file_path: str | Path, patterns: str) -> bool:
        """Check if a file matches the given patterns.

        Args:
            file_path: Path to the file to check
            patterns: Comma-separated list of glob patterns

        Returns:
            bool: True if file should be included, False if excluded
        """
        # Handle empty or whitespace-only patterns
        # 处理空字符串或纯空白字符串的情况
        if not patterns or patterns.isspace():
            return True

        path_str = str(file_path)
        file_name = Path(path_str).name
        # 将逗号分隔的模式字符串拆分为列表，并去除空白
        pattern_list: list[str] = [pattern.strip() for pattern in patterns.split(",") if pattern.strip()]

        # If no valid patterns after stripping, treat as include all
        # 去除空白后没有有效模式，默认包含所有文件
        if not pattern_list:
            return True

        # Process exclusion patterns first
        # 优先处理排除模式（以 ! 开头的模式）
        for pattern in pattern_list:
            if pattern.startswith("!"):
                # For exclusions, match against both full path and filename
                # 对排除模式，同时匹配完整路径和文件名
                exclude_pattern = pattern[1:]
                if fnmatch(path_str, exclude_pattern) or fnmatch(file_name, exclude_pattern):
                    return False

        # Then check inclusion patterns
        # 处理包含模式（不以 ! 开头的模式）
        include_patterns = [p for p in pattern_list if not p.startswith("!")]
        # If no include patterns, treat as include all
        # 没有包含模式时，默认包含所有文件
        if not include_patterns:
            return True

        # For inclusions, match against both full path and filename
        # 对包含模式，同时匹配完整路径和文件名
        return any(fnmatch(path_str, pattern) or fnmatch(file_name, pattern) for pattern in include_patterns)

    # 静态方法：检查文件内容是否匹配正则表达式
    @staticmethod
    def check_content_pattern(file_path: str | Path, pattern: str) -> bool:
        """Check if file content matches the given regex pattern.

        Args:
            file_path: Path to the file to check
            pattern: Regex pattern to match against content

        Returns:
            bool: True if content matches, False otherwise
        """
        try:
            # Check if file is binary
            # 检查文件是否为二进制文件
            with Path(file_path).open("rb") as file:
                content = file.read(1024)
                if b"\x00" in content:
                    return False

            # Try to compile the regex pattern first
            # 尝试编译正则表达式模式
            try:
                # Use the MULTILINE flag to better handle text content
                # 使用 MULTILINE 标志以便更好地处理多行文本
                content_regex = re.compile(pattern, re.MULTILINE)
                # Test the pattern with a simple string to catch syntax errors
                # 用简单字符串测试模式以捕获语法错误
                test_str = "test\nstring"
                if not content_regex.search(test_str):
                    # Pattern is valid but doesn't match test string
                    pass
            except (re.error, TypeError, ValueError):
                # 正则表达式编译失败，返回不匹配
                return False

            # If not binary and regex is valid, check content
            # 文件非二进制且正则表达式有效时，检查文件内容
            with Path(file_path).open(encoding="utf-8") as file:
                file_content = file.read()
            return bool(content_regex.search(file_content))
        except (OSError, UnicodeDecodeError):
            # 文件读取异常或编码错误时返回不匹配
            return False

    # 构建组合过滤函数：同时应用文件路径过滤和内容过滤
    def build_combined_filter(self, file_filter_patterns: str | None = None, content_filter_pattern: str | None = None):
        """Build a combined filter function from file and content patterns.

        Args:
            file_filter_patterns: Comma-separated glob patterns
            content_filter_pattern: Regex pattern for content

        Returns:
            callable: Filter function that takes a file path and returns bool
        """

        def combined_filter(file_path: str) -> bool:
            try:
                path = Path(file_path)

                # Check if file exists and is readable
                # 检查文件是否存在
                if not path.exists():
                    return False

                # Check if file is binary
                # 跳过二进制文件
                if self.is_binary(path):
                    return False

                # Apply file pattern filters
                # 应用文件路径模式过滤
                if file_filter_patterns and not self.check_file_patterns(path, file_filter_patterns):
                    return False

                # Apply content filter
                # 应用内容正则表达式过滤
                return not (content_filter_pattern and not self.check_content_pattern(path, content_filter_pattern))
            except Exception:  # noqa: BLE001
                # 异常情况下排除该文件
                return False

        return combined_filter

    # 异步上下文管理器：创建和清理临时克隆目录
    @asynccontextmanager
    async def temp_clone_dir(self):
        """Context manager for handling temporary clone directory."""
        temp_dir = None
        try:
            # 创建临时目录，前缀为 langflow_clone_
            temp_dir = tempfile.mkdtemp(prefix="langflow_clone_")
            yield temp_dir
        finally:
            # 退出上下文时删除临时目录
            if temp_dir:
                await anyio.Path(temp_dir).rmdir()

    # 动态更新组件构建配置：根据仓库来源显示/隐藏对应输入字段
    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None) -> dict:
        # Hide fields by default
        # 默认隐藏本地路径和克隆 URL 字段
        build_config["repo_path"]["show"] = False
        build_config["clone_url"]["show"] = False

        if field_name == "repo_source":
            if field_value == "Local":
                # 本地模式：显示路径输入，设为必填
                build_config["repo_path"]["show"] = True
                build_config["repo_path"]["required"] = True
                build_config["clone_url"]["required"] = False
            elif field_value == "Remote":
                # 远程模式：显示克隆 URL 输入，设为必填
                build_config["clone_url"]["show"] = True
                build_config["clone_url"]["required"] = True
                build_config["repo_path"]["required"] = False

        return build_config

    # 异步方法：构建 GitLoader 实例
    async def build_gitloader(self) -> GitLoader:
        # 获取文件过滤和内容过滤参数
        file_filter_patterns = getattr(self, "file_filter", None)
        content_filter_pattern = getattr(self, "content_filter", None)

        # 构建组合过滤函数
        combined_filter = self.build_combined_filter(file_filter_patterns, content_filter_pattern)

        # 根据来源类型获取仓库路径
        repo_source = getattr(self, "repo_source", None)
        if repo_source == "Local":
            # 本地模式：直接使用本地路径
            repo_path = self.repo_path
            clone_url = None
        else:
            # Clone source
            # 远程模式：使用临时目录进行克隆
            clone_url = self.clone_url
            async with self.temp_clone_dir() as temp_dir:
                repo_path = temp_dir

        # Only pass branch if it's explicitly set
        # 仅在明确设置分支时才传递分支参数
        branch = getattr(self, "branch", None)
        if not branch:
            branch = None

        # 创建并返回 GitLoader 实例
        return GitLoader(
            repo_path=repo_path,
            clone_url=clone_url if repo_source == "Remote" else None,
            branch=branch,
            file_filter=combined_filter,
        )

    # 主要输出方法：异步加载文档并转换为 Data 对象列表
    async def load_documents(self) -> list[Data]:
        gitloader = await self.build_gitloader()
        # 使用异步加载器惰性加载文档，转换为 Data 格式
        data = [Data.from_document(doc) async for doc in gitloader.alazy_load()]
        # 设置组件状态为加载到的数据
        self.status = data
        return data
