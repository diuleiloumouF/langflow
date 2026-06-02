"""Assistant service with validation and retry logic."""
# 助手服务，包含校验和重试逻辑

from __future__ import annotations

import asyncio
from contextlib import aclosing
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from lfx.log.logger import logger

from langflow.agentic.helpers.code_extraction import extract_component_code
from langflow.agentic.helpers.code_security import scan_code_security
from langflow.agentic.helpers.error_handling import extract_friendly_error
from langflow.agentic.helpers.input_sanitization import REFUSAL_MESSAGE, sanitize_input
from langflow.agentic.helpers.sse import (
    format_cancelled_event,
    format_complete_event,
    format_error_event,
    format_progress_event,
    format_token_event,
)
from langflow.agentic.helpers.streaming_retry import emit_execution_retry_events
from langflow.agentic.helpers.validation import validate_component_code, validate_component_runtime
from langflow.agentic.services.flow_executor import (
    execute_flow_file,
    execute_flow_file_streaming,
    extract_response_text,
)
from langflow.agentic.services.flow_types import (
    EXECUTION_RETRY_TEMPLATE,
    MAX_VALIDATION_RETRIES,
    OFF_TOPIC_REFUSAL_MESSAGE,
    VALIDATION_RETRY_TEMPLATE,
    VALIDATION_UI_DELAY_SECONDS,
    FlowExecutionError,
)
from langflow.agentic.services.helpers.intent_classification import classify_intent

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Coroutine

    from langflow.agentic.api.schemas import StepType


async def execute_flow_with_validation(
    flow_filename: str,
    input_value: str,
    global_variables: dict[str, str],
    *,
    max_retries: int = MAX_VALIDATION_RETRIES,
    user_id: str | None = None,
    session_id: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    api_key_var: str | None = None,
) -> dict:
    # 执行流程并校验生成的组件代码。
    # 如果响应中包含 Python 代码，则对代码进行校验。
    # 如果校验失败，将错误上下文反馈并重新执行流程。
    # 持续重试直到生成有效代码或达到最大重试次数。
    """Execute flow and validate the generated component code.

    If the response contains Python code, it validates the code.
    If validation fails, re-executes the flow with error context.
    Continues until valid code is generated or max retries reached.
    """
    # Layer 1: Input sanitization
    # 第一层：输入清洗，对用户输入进行安全过滤
    sanitization = sanitize_input(input_value)
    if not sanitization.is_safe:
        logger.warning(f"Input sanitization blocked request: {sanitization.violation}")
        # 输入清洗不通过，直接返回拒绝消息
        return {"result": REFUSAL_MESSAGE}

    current_input = sanitization.sanitized_input
    attempt = 0

    # 重试循环：最多执行 max_retries + 1 次
    while attempt <= max_retries:
        attempt += 1
        logger.info(f"Component generation attempt {attempt}/{max_retries + 1}")

        # 调用流程执行器，运行对应的流程文件
        result = await execute_flow_file(
            flow_filename=flow_filename,
            input_value=current_input,
            global_variables=global_variables,
            verbose=True,
            user_id=user_id,
            session_id=session_id,
            provider=provider,
            model_name=model_name,
            api_key_var=api_key_var,
        )

        # 从结果中提取响应文本
        response_text = extract_response_text(result)
        # 尝试从响应文本中提取 Python 组件代码
        code = extract_component_code(response_text)

        if not code:
            logger.debug("No Python code found in response, returning as-is")
            # 未找到 Python 代码，直接返回原始结果
            return result

        logger.info("Validating generated component code...")
        # 校验生成的组件代码是否合法
        validation = validate_component_code(code)

        # Layer 3: Security scan on generated code
        # 第三层：对生成的代码进行安全扫描
        security_result = scan_code_security(code)
        if not security_result.is_safe:
            violations_str = "; ".join(security_result.violations)
            logger.warning(f"Code security violations detected: {violations_str}")
            # 安全违规且已达最大重试次数，返回带错误信息的结果
            if attempt > max_retries:
                return {
                    **result,
                    "validated": False,
                    "validation_error": f"Security violations: {violations_str}",
                    "validation_attempts": attempt,
                }
            # 安全违规但还有重试机会，将错误上下文反馈给流程重试
            current_input = VALIDATION_RETRY_TEMPLATE.format(
                error=f"Security violations: {violations_str}. Do NOT use dangerous functions.",
                code=code,
            )
            continue

        if validation.is_valid:
            logger.info(f"Component '{validation.class_name}' validated successfully!")
            # 校验通过，返回验证成功的结果
            return {
                **result,
                "validated": True,
                "class_name": validation.class_name,
                "component_code": code,
                "validation_attempts": attempt,
            }

        logger.warning(f"Validation failed (attempt {attempt}): {validation.error}")

        if attempt > max_retries:
            logger.error(f"Max retries ({max_retries}) reached. Returning last result with error.")
            # 已达最大重试次数，返回最后的结果并附带错误信息
            return {
                **result,
                "validated": False,
                "validation_error": validation.error,
                "validation_attempts": attempt,
            }

        # 将校验失败的错误信息和代码作为上下文，供下次重试使用
        current_input = VALIDATION_RETRY_TEMPLATE.format(error=validation.error, code=code)
        logger.info("Retrying with error context...")

    # Safety return: the while loop always returns via internal checks above
    # 安全兜底返回：正常情况下 while 循环内部会通过 return 退出，此处在循环外提供兜底
    return {
        **result,
        "validated": False,
        "validation_error": validation.error,
        "validation_attempts": attempt,
    }


async def execute_flow_with_validation_streaming(
    flow_filename: str,
    input_value: str,
    global_variables: dict[str, str],
    *,
    max_retries: int = MAX_VALIDATION_RETRIES,
    user_id: str | None = None,
    session_id: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    api_key_var: str | None = None,
    is_disconnected: Callable[[], Coroutine[Any, Any, bool]] | None = None,
) -> AsyncGenerator[str, None]:
    # 执行流程并进行校验，以 SSE 流式事件（进度、token 等）的形式产出结果。
    #
    # SSE 事件流程：
    #     组件生成（通过分析用户输入检测）：
    #         1. generating_component - 展示推理界面（无 token 流式输出）
    #         2. extracting_code, validating 等步骤
    #
    #     问答：
    #         1. generating - LLM 正在生成响应
    #         1a. token 事件 - 实时 token 流式输出
    #         2. complete - 完成
    #
    # 注意：组件生成通过分析用户输入来判断。
    """Execute flow with validation, yielding SSE progress and token events.

    SSE Event Flow:
        For component generation (detected from user input):
            1. generating_component - Show reasoning UI (no token streaming)
            2. extracting_code, validating, etc.

        For Q&A:
            1. generating - LLM is generating response
            1a. token events - Real-time token streaming
            2. complete - Done

    Note: Component generation is detected by analyzing the user's input.
    """
    # Layer 1: Input sanitization (before any LLM call)
    # 第一层：输入清洗（在任何 LLM 调用之前执行）
    sanitization = sanitize_input(input_value)
    if not sanitization.is_safe:
        logger.warning(f"Input sanitization blocked request: {sanitization.violation}")
        yield format_complete_event({"result": REFUSAL_MESSAGE})
        return

    current_input = sanitization.sanitized_input

    # Classify intent using LLM (handles multi-language support)
    # This translates the input and determines if user wants to generate a component or ask a question
    # Use a separate session for intent classification to prevent
    # TranslationFlow messages from contaminating the assistant's memory
    # 使用 LLM 进行意图分类（支持多语言），判断用户是要生成组件还是提问
    # 使用独立会话进行意图分类，防止翻译流程的消息污染助手的记忆
    intent_result = await classify_intent(
        text=current_input,
        global_variables=global_variables,
        user_id=user_id,
        provider=provider,
        model_name=model_name,
        api_key_var=api_key_var,
    )

    # Layer 4: Off-topic rejection (saves LLM API costs)
    # 第四层：离题请求拒绝（节省 LLM API 调用成本）
    if intent_result.intent == "off_topic":
        logger.info("Off-topic request detected, returning refusal")
        yield format_complete_event({"result": OFF_TOPIC_REFUSAL_MESSAGE})
        return

    # Check if this is a component generation request based on LLM classification
    # 根据 LLM 分类结果判断是否为组件生成请求
    is_component_request = intent_result.intent == "generate_component"
    logger.info(f"Intent classification: {intent_result.intent} (is_component_request={is_component_request})")

    # Create cancel event for propagating cancellation to flow executor
    # 创建取消事件，用于向流程执行器传播取消信号
    cancel_event = asyncio.Event()

    # Helper to check if client disconnected
    # 辅助函数：检查客户端是否已断开连接
    async def check_cancelled() -> bool:
        if cancel_event.is_set():
            return True
        if is_disconnected is not None:
            return await is_disconnected()
        return False

    try:
        # max_retries=0 means 1 attempt (no retries), matching non-streaming semantics
        # 总尝试次数 = max_retries + 1（例如 max_retries=0 表示只执行 1 次，不重试）
        total_attempts = max_retries + 1

        for attempt in range(total_attempts):
            # Check if client disconnected before starting
            # 在开始前检查客户端是否已断开
            if await check_cancelled():
                logger.info("Client disconnected, cancelling generation")
                yield format_cancelled_event()
                return

            logger.debug(f"Starting attempt {attempt}, is_disconnected provided: {is_disconnected is not None}")

            # Step 1: Generating (different step name based on intent)
            # 步骤 1：生成中（根据意图显示不同的步骤名称）
            step_name: StepType = "generating_component" if is_component_request else "generating"
            yield format_progress_event(
                step_name,
                attempt + 1,
                total_attempts,
                message="Generating response...",
            )

            result = None
            cancelled = False
            execution_error: str | None = None
            # aclosing guarantees the async generator is closed on every exit path
            # (normal completion, exception, or cancellation) — not relying on GC.
            # aclosing 确保异步生成器在所有退出路径上都能被正确关闭
            # （正常完成、异常或取消），而不依赖垃圾回收机制。
            async with aclosing(
                execute_flow_file_streaming(
                    flow_filename=flow_filename,
                    input_value=current_input,
                    global_variables=global_variables,
                    user_id=user_id,
                    session_id=session_id,
                    provider=provider,
                    model_name=model_name,
                    api_key_var=api_key_var,
                    is_disconnected=is_disconnected,
                    cancel_event=cancel_event,
                )
            ) as flow_generator:
                try:
                    async for event_type, event_data in flow_generator:
                        if event_type == "token":
                            # Stream tokens for both Q&A and component generation
                            # For components, the frontend shows live code preview
                            # 流式输出 token，问答和组件生成均支持
                            # 组件生成时，前端会显示实时代码预览
                            yield format_token_event(event_data)
                        elif event_type == "end":
                            result = event_data
                        elif event_type == "cancelled":
                            logger.info("Flow execution cancelled by client disconnect")
                            cancelled = True
                            break
                except GeneratorExit:
                    logger.info("Assistant generator closed, setting cancel event")
                    # 生成器被关闭，设置取消事件以停止流程执行
                    cancel_event.set()
                    yield format_cancelled_event()
                    return
                except FlowExecutionError as e:
                    # Internal retry loop reads the raw error to pick a friendly message;
                    # the public HTTP detail stays generic (see FlowExecutionError docstring).
                    # 内部重试循环读取原始错误以选择友好的错误消息；
                    # 公开的 HTTP 详情保持通用（参见 FlowExecutionError 文档）。
                    execution_error = extract_friendly_error(e.original_error_message)
                except HTTPException as e:
                    execution_error = extract_friendly_error(str(e.detail))
                except (ValueError, RuntimeError, OSError) as e:
                    execution_error = extract_friendly_error(str(e))

            if cancelled:
                yield format_cancelled_event()
                return

            if execution_error is not None:
                logger.error(f"Flow execution failed (attempt {attempt + 1}): {execution_error}")

                # Q&A has no retry semantics — emit error and exit immediately
                # 问答模式没有重试语义——直接发送错误事件并退出
                if not is_component_request:
                    yield format_error_event(execution_error)
                    return

                # 发送执行重试相关事件
                async for event in emit_execution_retry_events(
                    attempt=attempt,
                    total_attempts=total_attempts,
                    error=execution_error,
                ):
                    yield event

                if attempt >= total_attempts - 1:
                    return  # complete event already emitted by the helper
                # 将错误上下文和原始输入组合，供下次重试使用
                current_input = EXECUTION_RETRY_TEMPLATE.format(
                    error=execution_error,
                    original_input=sanitization.sanitized_input,
                )
                continue

            if result is None:
                logger.error("Flow execution returned no result")
                yield format_error_event("Flow execution returned no result")
                return

            # Step 2: Generation complete
            # 步骤 2：生成完成
            yield format_progress_event(
                "generation_complete",
                attempt + 1,
                total_attempts,
                message="Response ready",
            )

            # For Q&A responses, return immediately without code extraction/validation.
            # This prevents example code snippets in explanatory answers from being
            # mistakenly treated as component generation results.
            # 问答响应直接返回，不进行代码提取和校验。
            # 这样可以防止解释性回答中的示例代码片段被误认为是组件生成结果。
            if not is_component_request:
                yield format_complete_event(result)
                return

            # Extract and validate component code from generation responses
            # 从生成的响应中提取组件代码
            response_text = extract_response_text(result)
            code = extract_component_code(response_text)

            if not code:
                # No code found even though user asked for component generation
                # 用户请求了组件生成但未找到代码，直接返回
                yield format_complete_event(result)
                return

            # Check for cancellation before extraction
            # 在代码提取前检查是否已取消
            if await check_cancelled():
                logger.info("Client disconnected before code extraction, cancelling")
                yield format_cancelled_event()
                return

            # Step 3: Extracting code (only shown when code is found)
            # 步骤 3：提取代码（仅在找到代码时显示）
            yield format_progress_event(
                "extracting_code",
                attempt + 1,
                total_attempts,
                message="Extracting Python code from response...",
            )
            await asyncio.sleep(VALIDATION_UI_DELAY_SECONDS)

            # Check for cancellation before validation
            # 在校验前检查是否已取消
            if await check_cancelled():
                logger.info("Client disconnected before validation, cancelling")
                yield format_cancelled_event()
                return

            # Step 4: Validating (include code so frontend can show preview)
            # 步骤 4：校验中（包含代码以便前端展示预览）
            yield format_progress_event(
                "validating",
                attempt + 1,
                total_attempts,
                message="Validating component code...",
                component_code=code,
            )
            await asyncio.sleep(VALIDATION_UI_DELAY_SECONDS)

            # 对生成的代码进行结构校验
            validation = validate_component_code(code)

            # Layer 3: Security scan on generated code
            # 第三层：对生成的代码进行安全扫描
            security_result = scan_code_security(code)
            if not security_result.is_safe:
                violations_str = "; ".join(security_result.violations)
                logger.warning(f"Code security violations detected: {violations_str}")
                # 发送安全违规事件
                yield format_progress_event(
                    "validation_failed",
                    attempt,
                    max_retries,
                    message="Security violations detected in generated code",
                    error=f"Security violations: {violations_str}",
                    component_code=code,
                )
                await asyncio.sleep(VALIDATION_UI_DELAY_SECONDS)

                # 已达最大重试次数，返回带安全错误的结果
                if attempt >= total_attempts - 1:
                    yield format_complete_event(
                        {
                            **result,
                            "validated": False,
                            "validation_error": f"Security violations: {violations_str}",
                            "validation_attempts": attempt + 1,
                            "component_code": code,
                        }
                    )
                    return

                # 发送重试事件，准备带安全上下文重试
                yield format_progress_event(
                    "retrying",
                    attempt,
                    max_retries,
                    message=f"Retrying with security context (attempt {attempt + 1}/{max_retries})...",
                    error=f"Security violations: {violations_str}",
                )
                await asyncio.sleep(VALIDATION_UI_DELAY_SECONDS)
                current_input = VALIDATION_RETRY_TEMPLATE.format(
                    error=f"Security violations: {violations_str}. "
                    "Do NOT use dangerous functions like os.system, subprocess, exec, eval. "
                    "Use Langflow's built-in integrations instead.",
                    code=code,
                )
                continue

            if validation.is_valid:
                # Runtime validation: instantiate AND execute the component's output
                # methods so pydantic-schema bugs (e.g. Data(data=[list])) are caught
                # before the component is handed to the user.
                # 运行时校验：实例化并执行组件的输出方法，
                # 以便在组件交给用户之前捕获 pydantic schema 相关的错误
                # （例如 Data(data=[list]) 这类问题）。
                runtime_error = await validate_component_runtime(code, user_id=user_id)
                if runtime_error:
                    logger.warning(f"Runtime validation failed (attempt {attempt}): {runtime_error}")
                    # 运行时校验失败，将校验结果标记为无效
                    validation = type(validation)(
                        is_valid=False,
                        code=code,
                        error=runtime_error,
                        class_name=validation.class_name,
                    )

            if validation.is_valid:
                logger.info(f"Component '{validation.class_name}' validated successfully")
                # 校验通过，发送验证成功事件
                yield format_progress_event(
                    "validated",
                    attempt,
                    max_retries,
                    message=f"Component '{validation.class_name}' validated successfully!",
                    class_name=validation.class_name,
                    component_code=code,
                )
                await asyncio.sleep(VALIDATION_UI_DELAY_SECONDS)

                yield format_complete_event(
                    {
                        **result,
                        "validated": True,
                        "class_name": validation.class_name,
                        "component_code": code,
                        "validation_attempts": attempt + 1,
                    }
                )
                return

            # Step 5b: Validation failed
            # 步骤 5b：校验失败
            logger.warning(f"Validation failed (attempt {attempt}): {validation.error}")
            yield format_progress_event(
                "validation_failed",
                attempt + 1,
                total_attempts,
                message="Validation failed",
                error=validation.error,
                class_name=validation.class_name,
                component_code=code,
            )
            await asyncio.sleep(VALIDATION_UI_DELAY_SECONDS)

            if attempt >= total_attempts - 1:
                # Max attempts reached, return with error
                # 已达最大尝试次数，返回带错误的结果
                yield format_complete_event(
                    {
                        **result,
                        "validated": False,
                        "validation_error": validation.error,
                        "validation_attempts": attempt + 1,
                        "component_code": code,
                    }
                )
                return

            # Step 6: Retrying
            # 步骤 6：重试中
            yield format_progress_event(
                "retrying",
                attempt + 1,
                total_attempts,
                message="Retrying with error context...",
                error=validation.error,
            )
            await asyncio.sleep(VALIDATION_UI_DELAY_SECONDS)

            # 将校验失败的错误信息和代码作为上下文，供下次重试使用
            current_input = VALIDATION_RETRY_TEMPLATE.format(error=validation.error, code=code)
    finally:
        # Always set cancel event when generator exits to stop any pending flow execution
        # 当生成器退出时始终设置取消事件，以停止任何待执行的流程
        logger.debug("Assistant generator exiting, setting cancel event")
        cancel_event.set()
