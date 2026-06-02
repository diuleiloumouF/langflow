import os
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles
import git

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output
from lfx.schema.data import Data
from lfx.schema.message import Message


# Git仓库提取器组件：克隆远程Git仓库并提取文件内容、目录结构、仓库信息和统计数据
class GitExtractorComponent(Component):
    display_name = "GitExtractor"
    # "分析Git仓库并返回文件内容和完整的仓库信息"
    description = "Analyzes a Git repository and returns file contents and complete repository information"
    icon = "GitLoader"

    # 组件输入：仓库URL
    inputs = [
        MessageTextInput(
            name="repository_url",
            display_name="Repository URL",
            # "Git仓库的URL（例如：https://github.com/username/repo）"
            info="URL of the Git repository (e.g., https://github.com/username/repo)",
            value="",
        ),
    ]

    # 组件输出：五种不同的提取结果
    outputs = [
        # 输出1：基于文本的文件内容（合并为单条消息，限300k字符）
        Output(
            display_name="Text-Based File Contents",
            name="text_based_file_contents",
            method="get_text_based_file_contents",
        ),
        # 输出2：目录结构（树形文本表示）
        Output(display_name="Directory Structure", name="directory_structure", method="get_directory_structure"),
        # 输出3：仓库基本信息（名称、分支、最新提交等）
        Output(display_name="Repository Info", name="repository_info", method="get_repository_info"),
        # 输出4：仓库统计信息（文件数、总大小、行数等）
        Output(display_name="Statistics", name="statistics", method="get_statistics"),
        # 输出5：所有文件内容（每文件一个Data对象）
        Output(display_name="Files Content", name="files_content", method="get_files_content"),
    ]

    @asynccontextmanager
    async def temp_git_repo(self):
        """Async context manager for temporary git repository cloning."""
        """异步上下文管理器：克隆仓库到临时目录，使用完毕后自动清理。"""
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        try:
            # Clone is still sync but wrapped in try/finally
            # 同步克隆仓库（GitPython不支持异步），包装在try/finally中确保清理
            git.Repo.clone_from(self.repository_url, temp_dir)
            yield temp_dir
        finally:
            # 无论成功或失败，都删除临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def get_repository_info(self) -> list[Data]:
        """获取仓库基本信息：名称、URL、默认分支、远程地址、最新提交、分支列表。"""
        try:
            async with self.temp_git_repo() as temp_dir:
                repo = git.Repo(temp_dir)
                # 构建仓库信息字典
                repo_info = {
                    # 从URL中提取仓库名称
                    "name": self.repository_url.split("/")[-1],
                    "url": self.repository_url,
                    # 当前活跃分支名
                    "default_branch": repo.active_branch.name,
                    # 所有远程仓库的URL
                    "remote_urls": [remote.url for remote in repo.remotes],
                    # 最新提交的详细信息
                    "last_commit": {
                        "hash": repo.head.commit.hexsha,
                        "author": str(repo.head.commit.author),
                        "message": repo.head.commit.message.strip(),
                        "date": str(repo.head.commit.committed_datetime),
                    },
                    # 所有本地分支
                    "branches": [str(branch) for branch in repo.branches],
                }
                result = [Data(data=repo_info)]
                self.status = result
                return result
        except git.GitError as e:
            error_result = [Data(data={"error": f"Error getting repository info: {e!s}"})]
            self.status = error_result
            return error_result

    async def get_statistics(self) -> list[Data]:
        """获取仓库统计信息：总文件数、总大小、总行数、二进制文件数、目录数。"""
        try:
            async with self.temp_git_repo() as temp_dir:
                total_files = 0
                total_size = 0
                total_lines = 0
                binary_files = 0
                directories = 0

                # 遍历仓库中所有文件，收集统计数据
                for root, dirs, files in os.walk(temp_dir):
                    total_files += len(files)
                    directories += len(dirs)
                    for file in files:
                        file_path = Path(root) / file
                        # 累加文件大小
                        total_size += file_path.stat().st_size
                        try:
                            # 尝试以UTF-8编码读取，计算行数
                            async with aiofiles.open(file_path, encoding="utf-8") as f:
                                total_lines += sum(1 for _ in await f.readlines())
                        except UnicodeDecodeError:
                            # 无法以UTF-8读取的文件视为二进制文件
                            binary_files += 1

                # 组装统计结果，同时提供KB和MB单位
                statistics = {
                    "total_files": total_files,
                    "total_size_bytes": total_size,
                    "total_size_kb": round(total_size / 1024, 2),
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "total_lines": total_lines,
                    "binary_files": binary_files,
                    "directories": directories,
                }
                result = [Data(data=statistics)]
                self.status = result
                return result
        except git.GitError as e:
            error_result = [Data(data={"error": f"Error calculating statistics: {e!s}"})]
            self.status = error_result
            return error_result

    async def get_directory_structure(self) -> Message:
        """获取仓库的目录结构，以树形文本格式返回。"""
        try:
            async with self.temp_git_repo() as temp_dir:
                tree = ["Directory structure:"]
                # 遍历仓库目录，构建树形结构文本
                for root, _dirs, files in os.walk(temp_dir):
                    # 通过路径分隔符计数计算当前层级深度
                    level = root.replace(temp_dir, "").count(os.sep)
                    # 根据层级设置缩进
                    indent = "    " * level
                    if level == 0:
                        tree.append(f"└── {Path(root).name}")
                    else:
                        tree.append(f"{indent}├── {Path(root).name}")
                    # 子文件使用更深一级的缩进
                    subindent = "    " * (level + 1)
                    tree.extend(f"{subindent}├── {f}" for f in files)
                directory_structure = "\n".join(tree)
                self.status = directory_structure
                return Message(text=directory_structure)
        except git.GitError as e:
            error_message = f"Error getting directory structure: {e!s}"
            self.status = error_message
            return Message(text=error_message)

    async def get_files_content(self) -> list[Data]:
        """获取仓库中所有文件的内容，每个文件返回一个Data对象（包含路径、大小、内容）。"""
        try:
            async with self.temp_git_repo() as temp_dir:
                content_list = []
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = Path(root) / file
                        # 计算相对于临时目录的相对路径
                        relative_path = file_path.relative_to(temp_dir)
                        file_size = file_path.stat().st_size
                        try:
                            async with aiofiles.open(file_path, encoding="utf-8") as f:
                                file_content = await f.read()
                        except UnicodeDecodeError:
                            # 二进制文件用占位符标记
                            file_content = "[BINARY FILE]"
                        content_list.append(
                            Data(data={"path": str(relative_path), "size": file_size, "content": file_content})
                        )
                self.status = content_list
                return content_list
        except git.GitError as e:
            error_result = [Data(data={"error": f"Error getting files content: {e!s}"})]
            self.status = error_result
            return error_result

    async def get_text_based_file_contents(self) -> Message:
        try:
            async with self.temp_git_repo() as temp_dir:
                content_list = ["(Files content cropped to 300k characters, download full ingest to see more)"]
                total_chars = 0
                char_limit = 300000

                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = Path(root) / file
                        relative_path = file_path.relative_to(temp_dir)
                        content_list.extend(["=" * 50, f"File: /{relative_path}", "=" * 50])

                        try:
                            async with aiofiles.open(file_path, encoding="utf-8") as f:
                                file_content = await f.read()
                                if total_chars + len(file_content) > char_limit:
                                    remaining_chars = char_limit - total_chars
                                    file_content = file_content[:remaining_chars] + "\n... (content truncated)"
                                content_list.append(file_content)
                                total_chars += len(file_content)
                        except UnicodeDecodeError:
                            content_list.append("[BINARY FILE]")

                        content_list.append("")

                        if total_chars >= char_limit:
                            break

                text_content = "\n".join(content_list)
                self.status = text_content
                return Message(text=text_content)
        except git.GitError as e:
            error_message = f"Error getting text-based file contents: {e!s}"
            self.status = error_message
            return Message(text=error_message)
