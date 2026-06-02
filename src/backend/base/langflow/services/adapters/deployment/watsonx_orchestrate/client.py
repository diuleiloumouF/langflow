"""Watsonx Orchestrate 适配器的客户端创建、身份验证和凭证解析。

该模块使用请求/执行上下文记忆化来管理 provider 客户端：
- `get_provider_clients()` 解析 provider 上下文和预构建的凭证/认证器。
- 生成的 `WxOClient` 在 ContextVar 中进行记忆化，作用域为当前异步执行上下文。
- 在同一上下文中使用相同的 `(provider_id, user_id)` 进行后续调用时，
  会复用同一个 `WxOClient` 实例，跳过重复的数据库/解密操作。

重要行为说明：
- ContextVar 状态是执行上下文作用域的（不是跨请求/全局状态）。
- 上下文只存储单个 `(key, client)` 条目，因为部署路由在每个请求路径中
  强制只允许一个 provider 上下文。
- 如果在同一上下文中请求不同的 `(provider_id, user_id)`，解析将失败。

Client creation, authentication, and credential resolution for the Watsonx Orchestrate adapter.

This module uses request/execution-context memoization for provider clients:

- `get_provider_clients()` resolves provider context and prebuilt credentials/authenticator.
- The resulting `WxOClient` is memoized in a ContextVar for the active async execution context.
- Subsequent calls with the same `(provider_id, user_id)` in that context reuse the same
  `WxOClient` instance and skip repeated DB/decryption work.

Important behavior notes:
- ContextVar state is execution-context scoped (not cross-request/global state).
- The context stores a single `(key, client)` entry because deployment routing enforces one
  provider context per request path.
- If a different `(provider_id, user_id)` is requested in the same context, resolution fails.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

# IBM 认证器和凭证类型导入
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, MCSPAuthenticator
from ibm_watsonx_orchestrate_core.types.connections import KeyValueConnectionCredentials
from lfx.services.adapters.deployment.exceptions import AuthSchemeError, CredentialResolutionError
from lfx.services.adapters.deployment.schema import EnvVarSource, EnvVarValueSpec, IdLike

from langflow.services.adapters.deployment.context import DeploymentProviderIDContext
from langflow.services.adapters.deployment.watsonx_orchestrate.constants import WxOAuthURL
from langflow.services.adapters.deployment.watsonx_orchestrate.types import WxOClient, WxOCredentials
from langflow.services.auth import utils as auth_utils
from langflow.services.database.models.deployment_provider_account.crud import get_provider_account_by_id
from langflow.services.deps import get_variable_service

if TYPE_CHECKING:
    from collections.abc import Iterator
    from contextvars import Token
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


# Watsonx Orchestrate Provider 客户端上下文数据类
# 用于存储 provider_id、user_id 和对应的 WxOClient 实例
@dataclass(frozen=True, slots=True)
class WxOProviderClientsContext:
    provider_id: str
    user_id: str
    clients: WxOClient


# Watsonx Orchestrate Provider 客户端请求上下文管理类
# 使用 ContextVar 在异步执行上下文中存储和管理 provider 客户端实例
class WxOProviderClientsRequestContext:
    _current: ClassVar[ContextVar[WxOProviderClientsContext | None]] = ContextVar(
        "langflow_wxo_provider_clients_request_context",
        default=None,
    )

    @classmethod
    def get_current(cls) -> WxOProviderClientsContext | None:
        return cls._current.get()

    @classmethod
    def set_current(cls, context: WxOProviderClientsContext) -> Token[WxOProviderClientsContext | None]:
        return cls._current.set(context)

    @classmethod
    def reset_current(cls, token: Token[WxOProviderClientsContext | None]) -> None:
        cls._current.reset(token)

    @classmethod
    def clear_current(cls) -> None:
        cls._current.set(None)

    @classmethod
    def push_null_boundary(cls) -> Token[WxOProviderClientsContext | None]:
        """推送一个全新的 ``None`` 槽位并返回用于 ``reset_current`` 的 Token。

        由 ``wxo_scope`` 使用，将所有权断言限定在一个
        ``deployment_provider_scope`` 条目内。

        Push a fresh ``None`` slot and return a Token for ``reset_current``.

        Used by ``wxo_scope`` to bound the ownership
        assertion to one ``deployment_provider_scope`` entry.
        """
        return cls._current.set(None)


# 生成 provider 客户端上下文键，用于 ContextVar 中的唯一标识
def _provider_client_context_key(*, provider_id: UUID, user_id: UUID | str) -> tuple[str, str]:
    return (str(provider_id), str(user_id))


def clear_provider_clients_request_context() -> None:
    """清除当前异步上下文中记忆化的 provider 客户端。

    主要用于测试和显式上下文生命周期控制。

    Clear execution-context memoized provider clients for the current async context.

    This is mainly useful in tests and explicit context lifecycle control.
    """
    WxOProviderClientsRequestContext.clear_current()


# 上下文管理器：将 WxO 客户端所有权断言的生命周期绑定到外层 provider 作用域
@contextmanager
def wxo_scope() -> Iterator[None]:
    """将 WxO 客户端所有权断言的生命周期绑定到外层 provider 作用域。

    进入时推送一个全新的 ``None`` 槽位，退出时通过 Token/reset 恢复先前的值，
    这样顺序/嵌套的 ``deployment_provider_scope(...)`` 块
    （例如 ``_sync_deployments_and_attachments_by_provider`` 中的每 provider 重试循环）
    不会相互影响。在单个作用域内，``_validate_request_context_provider_key`` 中的
    ``(provider_id, user_id)`` 所有权检查仍然有效。

    Bind the WxO client ownership assertion lifetime to the enclosing provider scope.

    Pushes a fresh ``None`` slot on entry and restores the prior value on exit
    via Token/reset, so sequential/nested ``deployment_provider_scope(...)`` blocks
    (e.g. the per-provider retry loop in ``_sync_deployments_and_attachments_by_provider``)
    cannot poison each other. The ``(provider_id, user_id)`` ownership check in
    ``_validate_request_context_provider_key`` remains in force *within* a single scope.
    """
    token = WxOProviderClientsRequestContext.push_null_boundary()
    try:
        yield
    finally:
        WxOProviderClientsRequestContext.reset_current(token)


# 获取当前执行上下文中记忆化的 provider 客户端
def get_request_context_provider_clients(*, provider_id: UUID, user_id: UUID | str) -> WxOClient | None:
    """返回当前活跃执行上下文中记忆化的 provider 客户端（如果存在）。

    在以下情况返回 `None`：
    - 此上下文中尚未记忆化任何 provider 客户端，或
    - 记忆化的条目属于不同的 `(provider_id, user_id)` 对。

    Return memoized provider clients for the active execution context, if present.

    Returns `None` when:
    - no provider clients have been memoized in this context yet, or
    - the memoized entry belongs to a different `(provider_id, user_id)` pair.
    """
    request_context = WxOProviderClientsRequestContext.get_current()
    if request_context is None:
        return None
    if (request_context.provider_id, request_context.user_id) == _provider_client_context_key(
        provider_id=provider_id,
        user_id=user_id,
    ):
        return request_context.clients
    return None


# 验证请求上下文中的 provider 键是否一致，防止混合 provider 解析
def _validate_request_context_provider_key(*, provider_id: UUID, user_id: UUID | str) -> None:
    request_context = WxOProviderClientsRequestContext.get_current()
    if request_context is None:
        return
    if (request_context.provider_id, request_context.user_id) != _provider_client_context_key(
        provider_id=provider_id,
        user_id=user_id,
    ):
        msg = (
            "A different deployment provider context was requested in the same execution context. "
            "This indicates an invalid mixed provider resolution flow."
        )
        raise CredentialResolutionError(message=msg)


# 在当前执行上下文中记忆化 provider 客户端
def set_request_context_provider_clients(*, provider_id: UUID, user_id: UUID | str, clients: WxOClient) -> None:
    """为活跃的执行上下文记忆化 provider 客户端。

    Memoize provider clients for the active execution context.
    """
    _validate_request_context_provider_key(provider_id=provider_id, user_id=user_id)
    context = WxOProviderClientsContext(
        provider_id=str(provider_id),
        user_id=str(user_id),
        clients=clients,
    )
    WxOProviderClientsRequestContext.set_current(context)


# 根据实例 URL 返回合适的 Watsonx Orchestrate API 认证器
def get_authenticator(instance_url: str, api_key: str) -> IAMAuthenticator | MCSPAuthenticator:
    """返回适用于 Watsonx Orchestrate API 的认证器。

    Return the appropriate authenticator for the Watsonx Orchestrate API.
    """
    if ".cloud.ibm.com" in instance_url:
        authenticator = IAMAuthenticator(apikey=api_key, url=WxOAuthURL.IBM_IAM.value)
    elif ".ibm.com" in instance_url:
        authenticator = MCSPAuthenticator(apikey=api_key, url=WxOAuthURL.MCSP.value)
    else:
        msg = f"Could not determine authentication scheme for instance URL: {instance_url}"
        raise AuthSchemeError(message=msg)

    # Use a split (connect, read) timeout so that cold-start TCP/TLS handshakes
    # fail fast instead of blocking for the SDK's default 60 s.
    authenticator.token_manager.http_config = {"timeout": (10, 30)}
    return authenticator


# 从部署 provider 账户解析 Watsonx Orchestrate 客户端凭证
async def resolve_wxo_client_credentials(
    *,
    user_id: UUID | str,
    db: AsyncSession,
    provider_id: UUID,
) -> WxOCredentials:
    """从部署 provider 账户解析 Watsonx Orchestrate 客户端凭证。

    解密后的 API 密钥仅用于实例化 SDK 认证器，不会保留在适配器凭证对象中。

    Resolve Watsonx Orchestrate client credentials from deployment provider account.

    The decrypted API key is used only to instantiate the SDK authenticator and is not
    retained in adapter credential objects.
    """
    try:
        provider_account = await get_provider_account_by_id(
            db,
            provider_id=provider_id,
            user_id=user_id,
        )
        if provider_account is None:
            msg = "Failed to find deployment provider account credentials."
            raise CredentialResolutionError(message=msg)

        instance_url = (provider_account.provider_url or "").strip()
        api_key = auth_utils.decrypt_api_key((provider_account.api_key or "").strip())
        if not instance_url or not api_key:
            msg = "Watsonx Orchestrate backend URL and API key must be configured."
            raise CredentialResolutionError(message=msg)

    except CredentialResolutionError:
        raise
    except Exception as exc:
        msg = "An unexpected error occurred while resolving Watsonx Orchestrate client credentials."
        raise CredentialResolutionError(message=msg) from exc

    authenticator = get_authenticator(instance_url=instance_url, api_key=api_key)
    return WxOCredentials(instance_url=instance_url, authenticator=authenticator)


# 获取并返回活跃部署 provider 上下文的 provider 客户端
async def get_provider_clients(
    *,
    user_id: UUID | str,
    db: AsyncSession,
) -> WxOClient:
    """解析并返回活跃部署 provider 上下文的 provider 客户端。

    快速路径：当 `(provider_id, user_id)` 匹配时返回执行上下文中记忆化的客户端。
    慢速路径：从数据库解析凭证，构建认证器，构造 `WxOClient`，然后进行记忆化。

    Resolve and return provider clients for the active deployment provider context.

    Fast-path: return execution-context memoized clients when `(provider_id, user_id)` matches.
    Slow-path: resolve credentials from DB, build authenticator, construct `WxOClient`, then memoize.
    """
    request_context = DeploymentProviderIDContext.get_current()
    if request_context is None:
        msg = "Deployment account context is not available for adapter resolution."
        raise CredentialResolutionError(message=msg)
    provider_id = request_context.provider_id
    _validate_request_context_provider_key(provider_id=provider_id, user_id=user_id)
    if context_clients := get_request_context_provider_clients(provider_id=provider_id, user_id=user_id):
        return context_clients

    credentials: WxOCredentials = await resolve_wxo_client_credentials(
        user_id=user_id,
        db=db,
        provider_id=provider_id,
    )

    clients = WxOClient(
        instance_url=credentials.instance_url,
        authenticator=credentials.authenticator,
    )
    set_request_context_provider_clients(provider_id=provider_id, user_id=user_id, clients=clients)
    return clients


# 从环境变量解析运行时凭证
async def resolve_runtime_credentials(
    *,
    user_id: IdLike,
    environment_variables: dict[str, EnvVarValueSpec],
    db: AsyncSession,
) -> KeyValueConnectionCredentials:
    """从环境变量解析运行时凭证。

    Resolve runtime credentials from environment variables.
    """
    resolved: dict[str, str] = {}
    for credential_key, env_var_value in environment_variables.items():
        resolved[credential_key] = await resolve_env_var_value(
            env_var_value,
            user_id=user_id,
            db=db,
        )
    return KeyValueConnectionCredentials(resolved)


# 解析环境变量值：如果是 RAW 类型直接返回，否则从变量服务解析
async def resolve_env_var_value(
    env_var_value: EnvVarValueSpec,
    *,
    user_id: IdLike,
    db: AsyncSession,
) -> str:
    if env_var_value.source == EnvVarSource.RAW:
        return env_var_value.value
    return await resolve_variable_value(
        env_var_value.value,
        user_id=user_id,
        db=db,
    )


# 从变量服务解析变量值，支持可选变量和默认值
async def resolve_variable_value(
    variable_name: str,
    *,
    user_id: UUID | str,
    db: AsyncSession,
    optional: bool = False,
    default_value: str | None = None,
) -> str:
    variable_service = get_variable_service()
    if variable_service is None:
        msg = "Variable service is not available."
        raise CredentialResolutionError(message=msg)
    try:
        value = await variable_service.get_variable(
            user_id=user_id,
            name=variable_name,
            field="value",
            session=db,
        )
        if value is not None:
            return value
    except CredentialResolutionError:
        raise
    except Exception as exc:
        if not optional:
            msg = "Failed to resolve a credential variable for the watsonx Orchestrate deployment provider."
            raise CredentialResolutionError(message=msg) from exc
    if optional:
        return default_value or ""
    msg = (
        "Failed to find a necessary credential for the "
        "watsonx Orchestrate deployment provider. "
        "Please ensure all credentials are provided and valid."
    )
    raise CredentialResolutionError(message=msg)
