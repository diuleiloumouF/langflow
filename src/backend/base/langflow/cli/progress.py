import platform
import sys
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import click

# 最小显示时长阈值（秒），低于此值的步骤不显示耗时
MIN_DURATION_THRESHOLD = 0.1  # Minimum duration to show in seconds (100ms)


# CLI 进度指示器，用于显示用户友好的分步进度
class ProgressIndicator:
    """A CLI progress indicator that shows user-friendly step-by-step progress.

    Shows animated loading indicators (□ → ■) for each step of the initialization process.
    """

    def __init__(self, *, verbose: bool = False):
        # 是否启用详细输出模式
        self.verbose = verbose
        # 步骤列表，每个步骤包含标题、描述、状态等信息
        self.steps: list[dict[str, Any]] = []
        # 当前正在执行的步骤索引
        self.current_step = 0
        # 是否正在运行动画
        self.running = False
        # 停止动画的标志
        self._stop_animation = False
        # 动画线程引用
        self._animation_thread: threading.Thread | None = None

        # 在 Windows 上使用安全的 ASCII 字符，防止编码问题
        if platform.system() == "Windows":
            self._animation_chars = ["-", "\\", "|", "/"]  # Windows 下的 ASCII 旋转字符
            self._success_icon = "+"  # Windows 下的成功图标（加号）
            self._failure_icon = "x"  # Windows 下的失败图标（叉号）
            self._farewell_emoji = ":)"  # Windows 下的告别表情（ASCII 笑脸）
        else:
            self._animation_chars = ["□", "▢", "▣", "■"]  # Unix 下的 Unicode 方块旋转字符
            self._success_icon = "✓"  # Unix 下的成功图标（对勾）
            self._failure_icon = "✗"  # Unix 下的失败图标（叉号）
            self._farewell_emoji = "👋"  # Unix 下的告别表情（挥手）

        # 动画字符索引，用于循环显示旋转动画
        self._animation_index = 0

    def add_step(self, title: str, description: str = "") -> None:
        """Add a step to the progress indicator."""
        # 向步骤列表添加一个新步骤
        self.steps.append(
            {
                "title": title,
                "description": description,
                "status": "pending",  # pending, running, completed, failed
                "start_time": None,
                "end_time": None,
            }
        )

    def _animate_step(self, step_index: int) -> None:
        """Animate the current step with rotating square characters."""
        # 步骤索引超出范围时直接返回
        if step_index >= len(self.steps):
            return

        step = self.steps[step_index]

        # 循环执行动画，直到步骤完成或动画被停止
        while self.running and step["status"] == "running" and not self._stop_animation:
            # 清除当前行并将光标移到行首
            sys.stdout.write("\r")

            # 显示当前动画字符
            animation_char = self._animation_chars[self._animation_index]

            # 打印带有动画的步骤信息
            line = f"{animation_char} {step['title']}..."
            sys.stdout.write(line)
            sys.stdout.flush()

            # 更新动画索引
            self._animation_index = (self._animation_index + 1) % len(self._animation_chars)

            time.sleep(0.15)  # 动画刷新速度

    def start_step(self, step_index: int) -> None:
        """Start a specific step and begin animation."""
        # 步骤索引超出范围时直接返回
        if step_index >= len(self.steps):
            return

        # 更新当前步骤并设置状态为运行中
        self.current_step = step_index
        step = self.steps[step_index]
        step["status"] = "running"
        step["start_time"] = time.time()

        self.running = True
        self._stop_animation = False

        # 在独立线程中启动动画
        self._animation_thread = threading.Thread(target=self._animate_step, args=(step_index,))
        self._animation_thread.daemon = True
        self._animation_thread.start()

    def complete_step(self, step_index: int, *, success: bool = True) -> None:
        """Complete a step and stop its animation."""
        # 步骤索引超出范围时直接返回
        if step_index >= len(self.steps):
            return

        # 更新步骤状态和结束时间
        step = self.steps[step_index]
        step["status"] = "completed" if success else "failed"
        step["end_time"] = time.time()

        # 停止动画
        self._stop_animation = True
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=0.5)

        self.running = False

        # 清除当前行并打印最终结果
        sys.stdout.write("\r")

        if success:
            icon = click.style(self._success_icon, fg="green", bold=True)
            title = click.style(step["title"], fg="green")
        else:
            icon = click.style(self._failure_icon, fg="red", bold=True)
            title = click.style(step["title"], fg="red")

        # 计算并格式化步骤耗时
        duration = ""
        if step["start_time"] and step["end_time"]:
            elapsed = step["end_time"] - step["start_time"]
            # 仅在详细模式且耗时超过阈值时显示耗时
            if self.verbose and elapsed > MIN_DURATION_THRESHOLD:  # Only show duration if verbose and > 100ms
                duration = click.style(f" ({elapsed:.2f}s)", fg="bright_black")

        line = f"{icon} {title}{duration}"
        click.echo(line)

    def fail_step(self, step_index: int, error_msg: str = "") -> None:
        """Mark a step as failed."""
        # 标记步骤为失败状态
        self.complete_step(step_index, success=False)
        # 详细模式下显示错误信息
        if error_msg and self.verbose:
            click.echo(click.style(f"   Error: {error_msg}", fg="red"))

    @contextmanager
    def step(self, step_index: int) -> Generator[None, None, None]:
        """Context manager for running a step with automatic completion."""
        # 上下文管理器：自动开始步骤、完成后自动标记成功/失败
        try:
            self.start_step(step_index)
            yield
            self.complete_step(step_index, success=True)
        except Exception as e:
            error_msg = str(e) if self.verbose else ""
            self.fail_step(step_index, error_msg)
            raise

    def print_summary(self) -> None:
        """Print a summary of all completed steps."""
        # 非详细模式下不打印摘要
        if not self.verbose:
            return

        # 获取已完成的步骤（包括成功和失败的）
        completed_steps = [s for s in self.steps if s["status"] in ["completed", "failed"]]
        if not completed_steps:
            return

        # 计算总耗时
        total_time = sum(
            (s["end_time"] - s["start_time"]) for s in completed_steps if s["start_time"] and s["end_time"]
        )

        click.echo()
        click.echo(click.style(f"Total initialization time: {total_time:.2f}s", fg="bright_black"))

    def print_shutdown_summary(self) -> None:
        """Print a summary of all completed shutdown steps."""
        # 非详细模式下不打印摘要
        if not self.verbose:
            return

        # 获取已完成的关闭步骤（包括成功和失败的）
        completed_steps = [s for s in self.steps if s["status"] in ["completed", "failed"]]
        if not completed_steps:
            return

        # 计算总关闭耗时
        total_time = sum(
            (s["end_time"] - s["start_time"]) for s in completed_steps if s["start_time"] and s["end_time"]
        )

        click.echo()
        click.echo(click.style(f"Total shutdown time: {total_time:.2f}s", fg="bright_black"))


def create_langflow_progress(*, verbose: bool = False) -> ProgressIndicator:
    """Create a progress indicator with predefined Langflow initialization steps."""
    # 创建带有预定义 Langflow 初始化步骤的进度指示器
    progress = ProgressIndicator(verbose=verbose)

    # 定义初始化步骤，顺序与 main.py 中一致
    steps = [
        ("Initializing Langflow", "Setting up basic configuration"),
        ("Checking Environment", "Loading environment variables and settings"),
        ("Starting Core Services", "Initializing database and core services"),
        ("Connecting Database", "Setting up database connection and migrations"),
        ("Loading Components", "Caching component types and custom components"),
        ("Adding Starter Projects", "Creating or updating starter project templates"),
        ("Launching Langflow", "Starting server and final setup"),
    ]

    for title, description in steps:
        progress.add_step(title, description)

    return progress


def create_langflow_shutdown_progress(*, verbose: bool = False, multiple_workers: bool = False) -> ProgressIndicator:
    """Create a progress indicator with predefined Langflow shutdown steps."""
    # 创建带有预定义 Langflow 关闭步骤的进度指示器
    progress = ProgressIndicator(verbose=verbose)

    # 定义关闭步骤，按初始化的逆序排列
    if multiple_workers:
        import os

        steps = [
            (f"[Worker PID {os.getpid()}] Stopping Server", "Gracefully stopping the web server"),
            (
                f"[Worker PID {os.getpid()}] Cancelling Background Tasks",
                "Stopping file synchronization and background jobs",
            ),
            (f"[Worker PID {os.getpid()}] Cleaning Up Services", "Teardown database connections and services"),
            (f"[Worker PID {os.getpid()}] Clearing Temporary Files", "Removing temporary directories and cache"),
            (f"[Worker PID {os.getpid()}] Finalizing Shutdown", "Completing cleanup and logging"),
        ]
    else:
        steps = [
            ("Stopping Server", "Gracefully stopping the web server"),
            ("Cancelling Background Tasks", "Stopping file synchronization and background jobs"),
            ("Cleaning Up Services", "Teardown database connections and services"),
            ("Clearing Temporary Files", "Removing temporary directories and cache"),
            ("Finalizing Shutdown", "Completing cleanup and logging"),
        ]

    for title, description in steps:
        progress.add_step(title, description)

    return progress
