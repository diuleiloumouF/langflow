"""Watsonx Orchestrate deployment payload contracts."""

from __future__ import annotations

from collections import Counter
from typing import Annotated, Any, Literal

from lfx.services.adapters.deployment.payloads import DeploymentPayloadSchemas
from lfx.services.adapters.deployment.schema import BaseFlowArtifact, EnvVarKey, EnvVarValueSpec, NormalizedId
from lfx.services.adapters.payload import AdapterPayload, PayloadSlot
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

# 原始工具名称类型：去除空白且最小长度为1的字符串
RawToolName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# 标准化字符串类型：去除空白且最小长度为1的字符串
NormalizedStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


# Watsonx 流程工件提供者数据
class WatsonxFlowArtifactProviderData(BaseModel):
    """Provider metadata for watsonx flow artifacts."""

    model_config = ConfigDict(extra="forbid")

    # Langflow 项目ID，用于 watsonx 快照创建
    project_id: NormalizedId = Field(description="Langflow project id carried for watsonx snapshot creation.")
    # 适配器中立的源引用，用于创建/更新快照关联
    source_ref: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Adapter-neutral source reference used for create/update snapshot correlation.",
    )


# Watsonx 连接原始载荷
class WatsonxConnectionRawPayload(BaseModel):
    """Connection payload for creating a new watsonx connection/config."""

    # 应用ID，用于操作引用，新创建的连接会保留此 app_id
    app_id: NormalizedId = Field(
        description=("App id used for operation references. Newly created connections preserve this app_id.")
    )
    # 环境变量字典
    environment_variables: dict[EnvVarKey, EnvVarValueSpec] | None = Field(None, description="Environment variables.")
    # 提供者特定的连接配置
    provider_config: AdapterPayload | None = Field(None, description="Provider-specific connection configuration.")


# Watsonx 更新工具
class WatsonxUpdateTools(BaseModel):
    """Tool pool available to update operations."""

    model_config = ConfigDict(extra="forbid")

    # 原始工具载荷列表，按 BaseFlowArtifact.name 索引
    raw_payloads: list[BaseFlowArtifact[WatsonxFlowArtifactProviderData]] | None = Field(
        default=None,
        description="Raw tool payloads keyed by BaseFlowArtifact.name.",
    )

    # 模型验证器：去重原始工具名称
    @model_validator(mode="after")
    def dedupe_raw_tool_names(self) -> WatsonxUpdateTools:
        raw_payloads = self.raw_payloads or []
        if not raw_payloads:
            return self
        deduped_by_name: dict[str, BaseFlowArtifact[WatsonxFlowArtifactProviderData]] = {}
        for payload in raw_payloads:
            deduped_by_name.setdefault(payload.name, payload)
        self.raw_payloads = list(deduped_by_name.values())
        return self


# Watsonx 更新连接
class WatsonxUpdateConnections(BaseModel):
    """Connection pool available to update operations."""

    model_config = ConfigDict(extra="forbid")

    # 原始连接载荷列表，按 app_id 索引，新创建的连接会保留此 app_id
    raw_payloads: list[WatsonxConnectionRawPayload] | None = Field(
        default=None,
        description=("Raw connection payloads keyed by app_id. Newly created connections preserve this app_id."),
    )

    # 模型验证器：验证原始 app_id 的唯一性
    @model_validator(mode="after")
    def validate_unique_raw_app_ids(self) -> WatsonxUpdateConnections:
        raw_payloads = self.raw_payloads or []
        app_id_counts = Counter(payload.app_id for payload in raw_payloads)
        duplicates = sorted(app_id for app_id, count in app_id_counts.items() if count > 1)
        if duplicates:
            msg = f"connections.raw_payloads contains duplicate app_id values: {duplicates}"
            raise ValueError(msg)
        return self


# 验证绑定操作引用
def _validate_bind_operation_references(
    *,
    operations: list[WatsonxBindOperation],
    raw_tool_names: set[str],
) -> set[str]:
    # 已引用的 app_id 集合
    referenced_app_ids: set[str] = set()
    for operation in operations:
        # 如果操作引用了原始工具名称，检查该名称是否存在于原始工具载荷中
        if operation.tool.name_of_raw is not None and operation.tool.name_of_raw not in raw_tool_names:
            msg = f"bind.tool.name_of_raw not found in tools.raw_payloads: [{operation.tool.name_of_raw!r}]"
            raise ValueError(msg)
        # 收集所有操作引用的 app_id
        for app_id in operation.app_ids:
            referenced_app_ids.add(app_id)
    return referenced_app_ids


# 验证工具引用一致性
def _validate_tool_ref_consistency(operations: list[Any]) -> None:
    """Reject conflicting source_ref values for the same tool_id across operations."""
    # 已见过的 tool_id -> source_ref 映射
    seen: dict[str, str] = {}
    for operation in operations:
        # 根据操作类型获取工具引用绑定
        ref: WatsonxToolRefBinding | None = None
        if isinstance(operation, WatsonxBindOperation):
            ref = operation.tool.tool_id_with_ref
        elif isinstance(operation, (WatsonxUnbindOperation, WatsonxRemoveToolOperation, WatsonxAttachToolOperation)):
            ref = operation.tool
        if ref is None:
            continue
        # 检查同一 tool_id 是否有冲突的 source_ref
        existing_source_ref = seen.get(ref.tool_id)
        if existing_source_ref is not None and existing_source_ref != ref.source_ref:
            msg = f"Conflicting source_ref for tool_id={ref.tool_id!r}: {existing_source_ref!r} vs {ref.source_ref!r}"
            raise ValueError(msg)
        seen[ref.tool_id] = ref.source_ref


# 验证重叠的现有工具操作
def _validate_overlapping_existing_tool_operations(operations: list[Any]) -> None:
    # 按工具分组的绑定 app_id
    bind_app_ids_by_tool: dict[str, set[str]] = {}
    # 按工具分组的解绑 app_id
    unbind_app_ids_by_tool: dict[str, set[str]] = {}
    # 已附加的工具ID集合
    attach_tool_ids: set[str] = set()
    # 已移除的工具ID集合
    remove_tool_ids: set[str] = set()

    for operation in operations:
        # 处理绑定操作：收集每个工具的绑定 app_id
        if isinstance(operation, WatsonxBindOperation):
            ref = operation.tool.tool_id_with_ref
            if ref is None:
                continue
            bind_app_ids_by_tool.setdefault(ref.tool_id, set()).update(operation.app_ids)
            continue

        # 处理附加操作：检查重复的附加工具操作
        if isinstance(operation, WatsonxAttachToolOperation):
            tool_id = operation.tool.tool_id
            if tool_id in attach_tool_ids:
                msg = f"Duplicate attach_tool operation for tool_id: [{tool_id!r}]"
                raise ValueError(msg)
            attach_tool_ids.add(tool_id)
            continue

        # 处理解绑操作：收集每个工具的解绑 app_id
        if isinstance(operation, WatsonxUnbindOperation):
            unbind_app_ids_by_tool.setdefault(operation.tool.tool_id, set()).update(operation.app_ids)
            continue

        # 处理移除操作：检查重复的移除工具操作
        if isinstance(operation, WatsonxRemoveToolOperation):
            tool_id = operation.tool.tool_id
            if tool_id in remove_tool_ids:
                msg = f"Duplicate remove_tool operation for tool_id: [{tool_id!r}]"
                raise ValueError(msg)
            remove_tool_ids.add(tool_id)
            continue

    # 检查附加操作与绑定操作之间的重叠
    bind_tool_ids = set(bind_app_ids_by_tool)
    overlap_attach_bind = sorted(attach_tool_ids.intersection(bind_tool_ids))
    if overlap_attach_bind:
        msg = (
            "attach_tool cannot be combined with bind.tool.tool_id_with_ref for the same tool_id(s): "
            f"{overlap_attach_bind}"
        )
        raise ValueError(msg)

    # 检查移除操作与绑定/附加/解绑操作之间的冲突
    for tool_id in sorted(remove_tool_ids):
        if tool_id in bind_tool_ids or tool_id in attach_tool_ids or tool_id in unbind_app_ids_by_tool:
            msg = f"remove_tool cannot be combined with bind/attach_tool/unbind for the same tool_id: [{tool_id!r}]"
            raise ValueError(msg)

    # 检查同一工具的绑定和解绑 app_id 是否重叠
    for tool_id, bind_app_ids in bind_app_ids_by_tool.items():
        overlap_app_ids = sorted(bind_app_ids.intersection(unbind_app_ids_by_tool.get(tool_id, set())))
        if overlap_app_ids:
            msg = f"bind and unbind app_ids overlap for the same tool_id [{tool_id!r}]: {overlap_app_ids}"
            raise ValueError(msg)


# 验证所有声明的 app_id 都被引用
def _validate_all_declared_app_ids_are_referenced(
    *,
    raw_app_ids: set[str],
    referenced_app_ids: set[str],
) -> None:
    # 找出未被引用的原始 app_id
    unused_raw_app_ids = sorted(raw_app_ids.difference(referenced_app_ids))
    if unused_raw_app_ids:
        msg = f"connections.raw_payloads contains app_id values not referenced by operations: {unused_raw_app_ids}"
        raise ValueError(msg)


# Watsonx 工具引用选择器
class WatsonxToolReference(BaseModel):
    """Tool selector for bind operations."""

    model_config = ConfigDict(extra="forbid")

    # 已存在的提供者工具引用，带有 source_ref 关联
    tool_id_with_ref: WatsonxToolRefBinding | None = Field(
        default=None,
        description="Existing provider tool reference with source_ref correlation.",
    )
    # tools.raw_payloads 中声明的工具条目名称
    name_of_raw: RawToolName | None = Field(
        default=None,
        description="Name of a tool entry declared in tools.raw_payloads.",
    )

    # 模型验证器：验证必须恰好提供一个选择器
    @model_validator(mode="after")
    def validate_exactly_one_selector(self) -> WatsonxToolReference:
        has_tool_id_with_ref = self.tool_id_with_ref is not None
        has_name_of_raw = self.name_of_raw is not None
        if has_tool_id_with_ref == has_name_of_raw:
            msg = "Exactly one of 'tool.tool_id_with_ref' or 'tool.name_of_raw' must be provided."
            raise ValueError(msg)
        return self


# Watsonx 绑定操作
class WatsonxBindOperation(BaseModel):
    """Bind a selected tool to app ids."""

    model_config = ConfigDict(extra="forbid")

    # 操作类型：绑定
    op: Literal["bind"]
    # 工具引用
    tool: WatsonxToolReference
    # 要绑定的应用ID列表，connections.raw_payloads 中的 app_id 引用新的原始连接，
    # 其他 app_id 被视为现有连接
    app_ids: list[NormalizedId] = Field(
        min_length=1,
        description=(
            "Operation app ids to bind. app_ids found in connections.raw_payloads "
            "reference new raw connections; all other app_ids are treated as existing connections."
        ),
    )

    # 字段验证器：去重应用ID
    @field_validator("app_ids")
    @classmethod
    def dedupe_app_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))


# Watsonx 解绑操作
class WatsonxUnbindOperation(BaseModel):
    """Unbind app connection from a tool."""

    model_config = ConfigDict(extra="forbid")

    # 操作类型：解绑
    op: Literal["unbind"]
    # 工具引用绑定，带有 source_ref 关联
    tool: WatsonxToolRefBinding = Field(description="Existing provider tool reference with source_ref correlation.")
    # 要解绑的应用ID列表，不能引用 connections.raw_payloads 中的 app_id
    app_ids: list[NormalizedId] = Field(
        min_length=1,
        description=("Operation app ids to unbind. Must not reference connections.raw_payloads app_ids."),
    )

    # 字段验证器：去重应用ID
    @field_validator("app_ids")
    @classmethod
    def dedupe_app_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))


# Watsonx 重命名工具操作
class WatsonxRenameToolOperation(BaseModel):
    """Rename a Langflow-managed tool on the provider."""

    model_config = ConfigDict(extra="forbid")

    # 操作类型：重命名工具
    op: Literal["rename_tool"]
    # 工具引用绑定，带有 source_ref 关联
    tool: WatsonxToolRefBinding = Field(
        description="Existing provider tool reference with source_ref correlation.",
    )
    # 新的工具名称
    new_name: str = Field(min_length=1, description="Validated wxO tool name.")


# Watsonx 移除工具操作
class WatsonxRemoveToolOperation(BaseModel):
    """Detach an existing tool from the deployment."""

    model_config = ConfigDict(extra="forbid")

    # 操作类型：移除工具
    op: Literal["remove_tool"]
    # 工具引用绑定，带有 source_ref 关联
    tool: WatsonxToolRefBinding = Field(
        description="Existing provider tool reference with source_ref correlation.",
    )


# Watsonx 附加工具操作
class WatsonxAttachToolOperation(BaseModel):
    """Attach an existing tool to the deployment without connection bindings."""

    model_config = ConfigDict(extra="forbid")

    # 操作类型：附加工具
    op: Literal["attach_tool"]
    # 工具引用绑定，带有 source_ref 关联
    tool: WatsonxToolRefBinding = Field(
        description="Existing provider tool reference with source_ref correlation.",
    )


# Watsonx 更新操作联合类型：绑定、解绑、重命名、移除或附加操作
WatsonxUpdateOperation = Annotated[
    WatsonxBindOperation
    | WatsonxUnbindOperation
    | WatsonxRenameToolOperation
    | WatsonxRemoveToolOperation
    | WatsonxAttachToolOperation,
    Field(discriminator="op"),
]

# Watsonx 创建操作联合类型：绑定或附加操作
WatsonxCreateOperation = Annotated[
    WatsonxBindOperation | WatsonxAttachToolOperation,
    Field(discriminator="op"),
]


# Watsonx 部署更新载荷
class WatsonxDeploymentUpdatePayload(BaseModel):
    """Watsonx provider_data contract for deployment update patch operations.

    Notes:
    - bind/unbind operations[*].app_ids are operation-side ids.
    - put_tools performs a standalone full replacement of the agent's tool
      list.  The agent will have exactly these tool IDs and no others.
      It cannot be combined with operations, tools, or connections
      (the validator rejects such payloads).
      This should only be used by rollback to restore pre-update
      attachment state.
    """

    model_config = ConfigDict(extra="forbid")

    # 工具更新载荷
    tools: WatsonxUpdateTools = Field(default_factory=WatsonxUpdateTools)
    # 连接更新载荷
    connections: WatsonxUpdateConnections = Field(default_factory=WatsonxUpdateConnections)
    # 更新操作列表
    operations: list[WatsonxUpdateOperation] = Field(default_factory=list)
    # 声明性工具ID列表，执行完全替换，不能与其他字段组合使用
    put_tools: list[NormalizedId] | None = Field(
        default=None,
        description=(
            "Declarative list of existing provider tool IDs the deployment should have. "
            "Performs a standalone full replacement of the agent's tool list — "
            "cannot be combined with operations, tools, or connections. "
            "This should only be used by rollback to restore pre-update attachment state."
        ),
    )
    # 提供者语言模型标识符，用于部署代理
    llm: NormalizedId | None = Field(
        default=None,
        description=("Provider language model identifier to use for the deployment agent."),
    )

    # 字段验证器：去重 put_tools
    @field_validator("put_tools")
    @classmethod
    def dedupe_put_tools(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return list(dict.fromkeys(value))

    # 属性：判断载荷是否包含工具级别变更
    @property
    def has_tool_work(self) -> bool:
        """Whether this payload includes tool-level mutations (put_tools, operations, or raw tool creation).

        The service layer uses this to decide between the lightweight
        spec-only update path and the full provider-plan path.
        """
        return bool(self.put_tools is not None or self.operations or self.tools.raw_payloads)

    # 模型验证器：验证是否有有效工作
    @model_validator(mode="after")
    def validate_has_work(self) -> WatsonxDeploymentUpdatePayload:
        if self.put_tools is not None:
            # put_tools 是完全替换，不能与其他字段组合使用
            has_other = self.operations or self.tools.raw_payloads or self.connections.raw_payloads
            if has_other:
                msg = "put_tools is a standalone full replacement and cannot be combined with other fields."
                raise ValueError(msg)
            return self
        if not self.operations:
            # 如果没有操作，检查连接是否需要操作引用
            has_connections = self.connections.raw_payloads
            if has_connections:
                msg = "connections require at least one bind/unbind operation that references app_ids."
                raise ValueError(msg)
            # Remaining valid no-operation cases:
            # - LLM-only update (no raw_payloads, no connections).
            # - raw_payloads without operations: tools are created and
            #   attached to the agent without connection bindings
            #   (connectionless-tool flow). The plan builder auto-creates
            #   entries for all declared raw_payloads even without explicit
            #   bind/attach_tool operations referencing them.
            # - empty/no-op provider_data can pass schema validation; the
            #   service layer rejects it when there are no spec updates.
            return self
        return self

    # 模型验证器：验证操作引用
    @model_validator(mode="after")
    def validate_operation_references(self) -> WatsonxDeploymentUpdatePayload:
        if self.put_tools is not None:
            return self
        # 获取原始工具名称集合
        raw_tool_names = {payload.name for payload in (self.tools.raw_payloads or [])}

        # 获取原始 app_id 集合
        raw_app_ids = {payload.app_id for payload in (self.connections.raw_payloads or [])}
        # 筛选绑定操作
        bind_operations = [operation for operation in self.operations if isinstance(operation, WatsonxBindOperation)]
        # 验证绑定操作引用并获取引用的 app_id
        referenced_app_ids = _validate_bind_operation_references(
            operations=bind_operations,
            raw_tool_names=raw_tool_names,
        )

        # 检查解绑操作是否引用了原始连接 app_id
        for operation in self.operations:
            if not isinstance(operation, WatsonxUnbindOperation):
                continue
            for app_id in operation.app_ids:
                referenced_app_ids.add(app_id)
                if app_id in raw_app_ids:
                    msg = f"unbind.operation app_ids must not reference connections.raw_payloads app_ids: [{app_id!r}]"
                    raise ValueError(msg)

        # 验证所有声明的 app_id 都被引用
        _validate_all_declared_app_ids_are_referenced(
            raw_app_ids=raw_app_ids,
            referenced_app_ids=referenced_app_ids,
        )
        # 验证工具引用一致性
        _validate_tool_ref_consistency(self.operations)
        # 验证重叠的现有工具操作
        _validate_overlapping_existing_tool_operations(self.operations)

        return self


# Watsonx 部署创建载荷
class WatsonxDeploymentCreatePayload(BaseModel):
    """Watsonx provider_data contract for deployment create operations."""

    model_config = ConfigDict(extra="forbid")

    # 工具更新载荷
    tools: WatsonxUpdateTools = Field(default_factory=WatsonxUpdateTools)
    # 连接更新载荷
    connections: WatsonxUpdateConnections = Field(default_factory=WatsonxUpdateConnections)
    # 创建操作列表
    operations: list[WatsonxCreateOperation] = Field(default_factory=list)
    # 提供者模型标识符，用于部署代理
    llm: NormalizedId = Field(description="Provider model identifier to use for the deployment agent.")

    # 模型验证器：验证是否有有效工作
    @model_validator(mode="after")
    def validate_has_work(self) -> WatsonxDeploymentCreatePayload:
        if not self.operations and not self.tools.raw_payloads:
            msg = "At least one bind/attach_tool operation or tools.raw_payloads entry must be provided for create."
            raise ValueError(msg)
        return self

    # 模型验证器：验证操作引用
    @model_validator(mode="after")
    def validate_operation_references(self) -> WatsonxDeploymentCreatePayload:
        # 获取原始工具名称集合
        raw_tool_names = {payload.name for payload in (self.tools.raw_payloads or [])}

        # 获取原始 app_id 集合
        raw_app_ids = {payload.app_id for payload in (self.connections.raw_payloads or [])}
        # 筛选绑定操作
        bind_operations = [operation for operation in self.operations if isinstance(operation, WatsonxBindOperation)]
        # 验证绑定操作引用并获取引用的 app_id
        referenced_app_ids = _validate_bind_operation_references(
            operations=bind_operations,
            raw_tool_names=raw_tool_names,
        )
        # 验证所有声明的 app_id 都被引用
        _validate_all_declared_app_ids_are_referenced(
            raw_app_ids=raw_app_ids,
            referenced_app_ids=referenced_app_ids,
        )
        # 验证工具引用一致性
        _validate_tool_ref_consistency(self.operations)
        # 验证重叠的现有工具操作
        _validate_overlapping_existing_tool_operations(self.operations)
        return self


class WatsonxToolRefBinding(BaseModel):
    """Correlates a source_ref (e.g. flow version id) with a provider tool_id.

    Used for both newly-created and pre-existing tools so callers can translate
    between adapter-level tool ids and higher-level source references.
    """

    model_config = ConfigDict(extra="forbid")

    source_ref: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    tool_id: NormalizedId


class WatsonxResultToolRefBinding(WatsonxToolRefBinding):
    """Tool ref binding with provenance flag for adapter results.

    Extends the base binding with a ``created`` flag so consumers can
    distinguish tools that were created during the operation from
    pre-existing tools whose refs were passed through for correlation.
    """

    created: bool = Field(description="True when the tool was created during this operation, False for pre-existing.")


class WatsonxDeploymentCreateResultData(BaseModel):
    """Normalized provider result payload for deployment create."""

    model_config = ConfigDict(extra="ignore")

    app_ids: list[NormalizedId] = Field(default_factory=list)
    tools_with_refs: list[WatsonxToolRefBinding] = Field(default_factory=list)
    tool_app_bindings: list[WatsonxToolAppBinding] = Field(default_factory=list)

    @field_validator("app_ids", mode="before")
    @classmethod
    def normalize_app_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        return [str(app_id).strip() for app_id in value if str(app_id).strip()]


class WatsonxToolAppBinding(BaseModel):
    """Normalized tool-app binding item for deployment result payloads."""

    model_config = ConfigDict(extra="forbid")

    tool_id: NormalizedId
    app_ids: list[NormalizedId] = Field(default_factory=list)

    @field_validator("app_ids", mode="before")
    @classmethod
    def normalize_app_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        return [str(app_id).strip() for app_id in value if str(app_id).strip()]


class WatsonxDeploymentUpdateResultData(BaseModel):
    """Normalized provider result payload for deployment update.

    Semantics:
    - ``created_snapshot_ids``: IDs of snapshot/tools created during this update.
    - ``added_snapshot_ids``: IDs of snapshot/tools newly attached to the agent
      by this update (includes ``created_snapshot_ids`` and newly attached
      pre-existing tools).
    - ``created_snapshot_bindings``: ``source_ref -> tool_id`` bindings for
      snapshots/tools created during this update.
    - ``added_snapshot_bindings``: ``source_ref -> tool_id`` bindings for
      snapshots/tools newly attached to the agent by this update.
    - ``removed_snapshot_bindings``: ``source_ref -> tool_id`` bindings for
      snapshots/tools detached from the agent by this update.
    - ``referenced_snapshot_bindings``: all operation-referenced bindings used
      for correlation/response shaping (includes created, added-existing,
      removed, and other touched existing refs).
    """

    model_config = ConfigDict(extra="ignore")

    created_app_ids: list[NormalizedId] = Field(default_factory=list)
    created_snapshot_ids: list[NormalizedId] = Field(default_factory=list)
    added_snapshot_ids: list[NormalizedId] = Field(default_factory=list)
    created_snapshot_bindings: list[WatsonxResultToolRefBinding] = Field(default_factory=list)
    # Newly attached snapshot/tool refs (created + newly attached existing).
    added_snapshot_bindings: list[WatsonxResultToolRefBinding] = Field(default_factory=list)
    # Detached snapshot/tool refs.
    removed_snapshot_bindings: list[WatsonxResultToolRefBinding] = Field(default_factory=list)
    # Full operation correlation set (created + existing refs).
    referenced_snapshot_bindings: list[WatsonxResultToolRefBinding] = Field(default_factory=list)
    tool_app_bindings: list[WatsonxToolAppBinding] | None = None

    @field_validator("created_app_ids", mode="before")
    @classmethod
    def normalize_created_app_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        return [str(app_id).strip() for app_id in value if str(app_id).strip()]

    @field_validator("created_snapshot_ids", mode="before")
    @classmethod
    def normalize_created_snapshot_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        return [str(snapshot_id).strip() for snapshot_id in value if str(snapshot_id).strip()]

    @field_validator("added_snapshot_ids", mode="before")
    @classmethod
    def normalize_added_snapshot_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        return [str(snapshot_id).strip() for snapshot_id in value if str(snapshot_id).strip()]


class WatsonxAgentExecutionResultData(BaseModel):
    """Normalized provider result payload for agent execution create/status."""

    model_config = ConfigDict(extra="allow")

    execution_id: NormalizedId | None = None
    agent_id: NormalizedId | None = Field(
        default=None,
        description="WXO agent identifier (resource_key in Langflow DB).",
    )
    thread_id: NormalizedId | None = None
    status: str | None = None
    result: Any | None = None
    started_at: str | None = None
    completed_at: str | None = None
    failed_at: str | None = None
    cancelled_at: str | None = None
    last_error: str | None = None


class WatsonxModelOut(BaseModel):
    """Model metadata returned by wxO model catalog endpoints."""

    model_config = ConfigDict(extra="ignore")

    model_name: NormalizedId


class WatsonxDeploymentLlmListResultData(BaseModel):
    """Normalized provider result payload for deployment LLM listing."""

    model_config = ConfigDict(extra="forbid")

    models: list[WatsonxModelOut] = Field(default_factory=list)


class WatsonxSnapshotConnectionsProviderData(BaseModel):
    """Provider data contract for snapshot list items in snapshot-ids mode."""

    model_config = ConfigDict(extra="forbid")

    connections: dict[NormalizedId, NormalizedId] = Field(default_factory=dict)


class WatsonxConfigItemProviderData(BaseModel):
    """Provider data contract for config list items."""

    model_config = ConfigDict(extra="forbid")

    type: NormalizedStr
    environment: NormalizedStr


class WatsonxConfigListResultData(BaseModel):
    """Provider-result metadata contract for config listing.

    ``deployment_id`` is present for deployment-scoped listings and absent for
    tenant-scoped listings.
    """

    model_config = ConfigDict(extra="forbid")

    deployment_id: NormalizedId | None = None
    tool_ids: list[NormalizedId] | None = None


class WatsonxSnapshotListResultData(BaseModel):
    """Provider-result metadata contract for snapshot listing.

    ``deployment_id`` is present for deployment-scoped listings and absent for
    tenant-scoped listings.
    """

    model_config = ConfigDict(extra="forbid")

    deployment_id: NormalizedId | None = None


class WatsonxProviderUpdateApplyResult(BaseModel):
    """Public adapter contract for update helper apply results.

    Field semantics match ``WatsonxDeploymentUpdateResultData``.
    """

    model_config = ConfigDict(extra="forbid")

    created_app_ids: list[NormalizedId] = Field(default_factory=list)
    created_snapshot_ids: list[NormalizedId] = Field(default_factory=list)
    added_snapshot_ids: list[NormalizedId] = Field(default_factory=list)
    created_snapshot_bindings: list[WatsonxResultToolRefBinding] = Field(default_factory=list)
    # Newly attached snapshot/tool refs (created + newly attached existing).
    added_snapshot_bindings: list[WatsonxResultToolRefBinding] = Field(default_factory=list)
    # Detached snapshot/tool refs.
    removed_snapshot_bindings: list[WatsonxResultToolRefBinding] = Field(default_factory=list)
    # Full operation correlation set (created + existing refs).
    referenced_snapshot_bindings: list[WatsonxResultToolRefBinding] = Field(default_factory=list)


class WatsonxProviderCreateApplyResult(BaseModel):
    """Public adapter contract for create helper apply results."""

    model_config = ConfigDict(extra="forbid")

    agent_id: NormalizedId
    app_ids: list[NormalizedId] = Field(default_factory=list)
    tools_with_refs: list[WatsonxToolRefBinding] = Field(default_factory=list)
    tool_app_bindings: list[WatsonxToolAppBinding] = Field(default_factory=list)
    deployment_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    display_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class WatsonxVerifyCredentialsPayload(BaseModel):
    """WXO credential shape for provider account verification."""

    model_config = ConfigDict(extra="forbid")

    api_key: str


# Canonical watsonx deployment payload registry. Adapter service and mapper
# consume this same object to keep slot ownership explicit and avoid drift.
PAYLOAD_SCHEMAS = DeploymentPayloadSchemas(
    deployment_create=PayloadSlot(WatsonxDeploymentCreatePayload),
    flow_artifact=PayloadSlot(WatsonxFlowArtifactProviderData),
    snapshot_item_data=PayloadSlot(WatsonxSnapshotConnectionsProviderData),
    config_item_data=PayloadSlot(WatsonxConfigItemProviderData),
    deployment_create_result=PayloadSlot(WatsonxDeploymentCreateResultData),
    deployment_update=PayloadSlot(WatsonxDeploymentUpdatePayload),
    deployment_update_result=PayloadSlot(WatsonxDeploymentUpdateResultData),
    execution_create_result=PayloadSlot(WatsonxAgentExecutionResultData),
    execution_status_result=PayloadSlot(WatsonxAgentExecutionResultData),
    deployment_llm_list_result=PayloadSlot(WatsonxDeploymentLlmListResultData),
    config_list_result=PayloadSlot(WatsonxConfigListResultData),
    snapshot_list_result=PayloadSlot(WatsonxSnapshotListResultData),
    verify_credentials=PayloadSlot(WatsonxVerifyCredentialsPayload),
)
