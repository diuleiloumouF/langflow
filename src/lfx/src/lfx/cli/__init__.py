"""LFX CLI module for serving flows."""
# LFX CLI 模块，用于提供流（flow）服务。

__all__ = ["serve_command"]


def __getattr__(name: str):
    """Lazy import for serve_command."""
    # 惰性导入 serve_command，避免在模块加载时立即引入依赖。
    if name == "serve_command":
        from lfx.cli.commands import serve_command

        return serve_command
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
