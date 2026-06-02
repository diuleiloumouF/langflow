"""CLI commands for LFX."""

# LFX 的 CLI 命令模块，提供 flow 的 serve、run 等命令行接口

from __future__ import annotations

import json
import os
import sys
import tempfile
from functools import partial
from pathlib import Path

import typer
import uvicorn
from asyncer import syncify
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from lfx.cli.common import (
    create_verbose_printer,
    flow_id_from_path,
    get_api_key,
    get_best_access_host,
    get_free_port,
    is_port_in_use,
    load_graph_from_path,
)
from lfx.cli.serve_app import FlowMeta, create_multi_serve_app

# 初始化 Rich 控制台，用于终端美化输出
console = Console()

# 常量
# API Key 显示时的掩码长度，超过此长度的部分用省略号替代
API_KEY_MASK_LENGTH = 8


# serve 命令入口，将异步函数通过 syncify 转为同步，以便 typer 框架调用
@partial(syncify, raise_sync_error=False)
async def serve_command(
    script_path: str | None = typer.Argument(
        None,
        help=(
            "Path to JSON flow (.json) or Python script (.py) file or stdin input. "
            "Optional when using --flow-json or --stdin."
        ),
    ),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind the server to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind the server to"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show diagnostic output and execution details"),  # noqa: FBT001, FBT003
    env_file: Path | None = typer.Option(
        None,
        "--env-file",
        help="Path to the .env file containing environment variables",
    ),
    log_level: str = typer.Option(
        "warning",
        "--log-level",
        help="Logging level. One of: debug, info, warning, error, critical",
    ),
    flow_json: str | None = typer.Option(
        None,
        "--flow-json",
        help="Inline JSON flow content as a string (alternative to script_path)",
    ),
    *,
    stdin: bool = typer.Option(
        False,  # noqa: FBT003
        "--stdin",
        help="Read JSON flow content from stdin (alternative to script_path)",
    ),
    check_variables: bool = typer.Option(
        True,  # noqa: FBT003
        "--check-variables/--no-check-variables",
        help="Check global variables for environment compatibility",
    ),
) -> None:
    """Serve LFX flows as a web API.

    Supports single files, inline JSON, and stdin input.

    Examples:
        # Serve from file
        lfx serve my_flow.json

        # Serve inline JSON
        lfx serve --flow-json '{"nodes": [...], "edges": [...]}'

        # Serve from stdin
        cat my_flow.json | lfx serve --stdin
        echo '{"nodes": [...]}' | lfx serve --stdin
    """
    # 使用指定的日志级别配置日志，并导入 logger
    from lfx.log.logger import configure, logger

    configure(log_level=log_level)

    # 创建详细输出打印器，根据 verbose 标志决定是否输出调试信息
    verbose_print = create_verbose_printer(verbose=verbose)

    # 验证输入源 - 必须且只能提供一种输入方式：文件路径、内联 JSON 或标准输入
    input_sources = [script_path is not None, flow_json is not None, stdin]
    if sum(input_sources) != 1:
        if sum(input_sources) == 0:
            verbose_print("Error: Must provide either script_path, --flow-json, or --stdin")
        else:
            verbose_print("Error: Cannot use script_path, --flow-json, and --stdin together. Choose exactly one.")
        raise typer.Exit(1)

    # 如果提供了 .env 文件，加载其中的环境变量
    if env_file:
        if not env_file.exists():
            verbose_print(f"Error: Environment file '{env_file}' does not exist.")
            raise typer.Exit(1)

        verbose_print(f"Loading environment variables from: {env_file}")
        load_dotenv(env_file)

    # 验证 API Key 是否已配置
    try:
        api_key = get_api_key()
        verbose_print("✓ LANGFLOW_API_KEY is configured")
    except ValueError as e:
        typer.echo(f"✗ {e}", err=True)
        typer.echo("Set the LANGFLOW_API_KEY environment variable before serving.", err=True)
        raise typer.Exit(1) from e

    # 验证日志级别是否合法
    valid_log_levels = {"debug", "info", "warning", "error", "critical"}
    if log_level.lower() not in valid_log_levels:
        verbose_print(f"Error: Invalid log level '{log_level}'. Must be one of: {', '.join(sorted(valid_log_levels))}")
        raise typer.Exit(1)

    # 使用指定的日志级别配置日志
    # 禁用 serve 命令的美化日志，避免 API 响应中出现 ANSI 转义码
    os.environ["LANGFLOW_PRETTY_LOGS"] = "false"
    verbose_print(f"Configuring logging with level: {log_level}")
    from lfx.log.logger import configure

    configure(log_level=log_level)

    # ------------------------------------------------------------------
    # 处理内联 JSON 内容或标准输入
    # ------------------------------------------------------------------
    # 需要清理的临时文件路径（用于内联 JSON 或 stdin 输入时创建的临时文件）
    temp_file_to_cleanup = None

    if flow_json is not None:
        # 处理通过 --flow-json 参数传入的内联 JSON 内容
        logger.info("Processing inline JSON content...")
        try:
            # 验证 JSON 语法是否正确
            json_data = json.loads(flow_json)
            logger.info("JSON content is valid")

            # 将 JSON 内容写入临时文件，以便后续统一处理
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
                json.dump(json_data, temp_file, indent=2)
                temp_file_to_cleanup = temp_file.name

            script_path = temp_file_to_cleanup
            logger.info(f"Created temporary file: {script_path}")

        except json.JSONDecodeError as e:
            typer.echo(f"Error: Invalid JSON content: {e}", err=True)
            raise typer.Exit(1) from e
        except Exception as e:
            verbose_print(f"Error processing JSON content: {e}")
            raise typer.Exit(1) from e

    elif stdin:
        # 处理通过标准输入管道传入的 JSON 内容
        logger.info("Reading JSON content from stdin...")
        try:
            # 读取标准输入的全部内容
            stdin_content = sys.stdin.read().strip()
            if not stdin_content:
                logger.error("No content received from stdin")
                raise typer.Exit(1)

            # 验证 JSON 语法是否正确
            json_data = json.loads(stdin_content)
            logger.info("JSON content from stdin is valid")

            # 将 JSON 内容写入临时文件，以便后续统一处理
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
                json.dump(json_data, temp_file, indent=2)
                temp_file_to_cleanup = temp_file.name

            script_path = temp_file_to_cleanup
            logger.info(f"Created temporary file from stdin: {script_path}")

        except json.JSONDecodeError as e:
            verbose_print(f"Error: Invalid JSON content from stdin: {e}")
            raise typer.Exit(1) from e
        except Exception as e:
            verbose_print(f"Error reading from stdin: {e}")
            raise typer.Exit(1) from e

    try:
        # Load the graph
        if script_path is None:
            verbose_print("Error: script_path is None after input validation")
            raise typer.Exit(1)

        resolved_path = Path(script_path).resolve()

        if not resolved_path.exists():
            typer.echo(f"Error: File '{resolved_path}' does not exist.", err=True)
            raise typer.Exit(1)

        if resolved_path.suffix == ".json":
            graph = await load_graph_from_path(resolved_path, resolved_path.suffix, verbose_print, verbose=verbose)
        elif resolved_path.suffix == ".py":
            verbose_print("Loading graph from Python script...")
            from lfx.cli.script_loader import load_graph_from_script

            graph = await load_graph_from_script(resolved_path)
            verbose_print("✓ Graph loaded from Python script")
        else:
            err_msg = "Error: Only JSON flow files (.json) or Python scripts (.py) are supported. "
            err_msg += f"Got: {resolved_path.suffix}"
            verbose_print(err_msg)
            raise typer.Exit(1)

        # Prepare the graph
        logger.info("Preparing graph for serving...")
        try:
            graph.prepare()
            logger.info("Graph prepared successfully")

            # Validate global variables for environment compatibility
            if check_variables:
                from lfx.cli.validation import validate_global_variables_for_env

                validation_errors = validate_global_variables_for_env(graph)
                if validation_errors:
                    logger.error("Global variable validation failed:")
                    for error in validation_errors:
                        logger.error(f"  - {error}")
                    raise typer.Exit(1)
            else:
                logger.info("Global variable validation skipped")
        except Exception as e:
            verbose_print(f"✗ Failed to prepare graph: {e}")
            raise typer.Exit(1) from e

        # Check if port is in use
        if is_port_in_use(port, host):
            available_port = get_free_port(port)
            if verbose:
                verbose_print(f"Port {port} is in use, using port {available_port} instead")
            port = available_port

        # Create single-flow metadata
        flow_id = flow_id_from_path(resolved_path, resolved_path.parent)
        graph.flow_id = flow_id  # annotate graph for reference

        title = resolved_path.stem
        description = None

        metas = {
            flow_id: FlowMeta(
                id=flow_id,
                relative_path=str(resolved_path.name),
                title=title,
                description=description,
            )
        }
        graphs = {flow_id: graph}

        source_display = "inline JSON" if flow_json else "stdin" if stdin else str(resolved_path)
        verbose_print(f"✓ Prepared single flow '{title}' from {source_display} (id={flow_id})")

        # Create FastAPI app
        serve_app = create_multi_serve_app(
            root_dir=resolved_path.parent,
            graphs=graphs,
            metas=metas,
            verbose_print=verbose_print,
        )

        verbose_print("🚀 Starting single-flow server...")

        protocol = "http"
        access_host = get_best_access_host(host)

        masked_key = f"{api_key[:API_KEY_MASK_LENGTH]}..." if len(api_key) > API_KEY_MASK_LENGTH else "***"

        console.print()
        console.print(
            Panel.fit(
                f"[bold green]🎯 Single Flow Served Successfully![/bold green]\n\n"
                f"[bold]Source:[/bold] {source_display}\n"
                f"[bold]Server:[/bold] {protocol}://{access_host}:{port}\n"
                f"[bold]API Key:[/bold] {masked_key}\n\n"
                f"[dim]Send POST requests to:[/dim]\n"
                f"[blue]{protocol}://{access_host}:{port}/flows/{flow_id}/run[/blue]\n\n"
                f"[dim]With headers:[/dim]\n"
                f"[blue]x-api-key: {masked_key}[/blue]\n\n"
                f"[dim]Or query parameter:[/dim]\n"
                f"[blue]?x-api-key={masked_key}[/blue]\n\n"
                f"[dim]Request body:[/dim]\n"
                f"[blue]{{'input_value': 'Your input message'}}[/blue]",
                title="[bold blue]LFX Server[/bold blue]",
                border_style="blue",
            )
        )
        console.print()

        # Start the server
        # Use uvicorn.Server to properly handle async context
        # uvicorn.run() uses asyncio.run() internally which fails when
        # an event loop is already running (due to syncify decorator)
        try:
            config = uvicorn.Config(
                serve_app,
                host=host,
                port=port,
                log_level=log_level,
            )
            server = uvicorn.Server(config)
            await server.serve()
        except KeyboardInterrupt:
            verbose_print("\n👋 Server stopped")
            raise typer.Exit(0) from None
        except Exception as e:
            verbose_print(f"✗ Failed to start server: {e}")
            raise typer.Exit(1) from e

    finally:
        # Clean up temporary file if created
        if temp_file_to_cleanup:
            try:
                Path(temp_file_to_cleanup).unlink()
                verbose_print(f"✓ Cleaned up temporary file: {temp_file_to_cleanup}")
            except OSError as e:
                verbose_print(f"Warning: Failed to clean up temporary file {temp_file_to_cleanup}: {e}")
