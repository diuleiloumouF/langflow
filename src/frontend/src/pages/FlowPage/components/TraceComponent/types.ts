import { CellClickedEvent } from "ag-grid-community";
import { TraceListItem } from "@/controllers/API/queries/traces/types";
import { createFlowTracesColumns } from "./config/flowTraceColumns";

/** Span 类型枚举 */
export type SpanType =
  | "chain"
  | "llm"
  | "tool"
  | "retriever"
  | "embedding"
  | "parser"
  | "agent"
  | "none";

/** Span 状态枚举 */
export type SpanStatus = "unset" | "ok" | "error";

/** Token 用量信息 */
export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  cost: number;
}

/** Span 数据结构，表示追踪树中的单个执行节点 */
export interface Span {
  id: string;
  name: string;
  type: SpanType;
  status: SpanStatus;
  startTime: string;
  endTime?: string;
  latencyMs: number;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  error?: string;
  modelName?: string;
  tokenUsage?: TokenUsage;
  children: Span[];
}

/** 追踪数据结构，包含完整的执行追踪信息 */
export interface Trace {
  id: string;
  name: string;
  status: SpanStatus;
  startTime: string;
  endTime?: string;
  totalLatencyMs: number;
  totalTokens: number;
  totalCost: number;
  flowId: string;
  sessionId: string;
  input: Record<string, unknown> | null;
  output: Record<string, unknown> | null;
  spans: Span[];
}

/** Span 树节点组件的属性定义 */
export interface SpanNodeProps {
  span: Span;
  depth: number;
  isExpanded: boolean;
  isSelected: boolean;
  onToggle: () => void;
  onSelect: () => void;
}

/** Span 详情面板组件的属性定义 */
export interface SpanDetailProps {
  span: Span | null;
}

/** 追踪视图组件的属性定义 */
export interface TraceViewProps {
  flowId?: string | null;
  initialTraceId?: string | null;
  onTraceClick?: (traceId: string) => void;
}

/** 追踪详情视图组件的属性定义 */
export interface TraceDetailViewProps {
  traceId: string | null;
  flowName?: string | null;
}

/** 追踪手风琴项组件的属性定义 */
export interface TraceAccordionItemProps {
  traceId: string;
  traceName: string;
  traceStatus: string;
  traceStartTime: string;
  totalLatencyMs: number;
  totalTokens: number;
  totalCost: number;
  sessionId: string;
  input: Record<string, unknown> | null;
  output: Record<string, unknown> | null;
  isExpanded: boolean;
  onTraceClick?: (traceId: string) => void;
}

/** 状态图标属性类型 */
export type StatusIconProps = {
  colorClass: string;
  iconName: "Loader2" | "CircleCheck" | "CircleX";
  shouldSpin: boolean;
};

/** 分组会话渲染属性类型 */
export type RenderGroupedSessionType = {
  isLoading: boolean;
  groupedRows: Array<[string, TraceListItem[]]>;
  columns: ReturnType<typeof createFlowTracesColumns>;
  expandedSessionIds: string[];
  handleCellClicked: (event: CellClickedEvent) => void;
};

/** 日期范围选择器组件的属性定义 */
export type DateRangePopoverProps = {
  startDate: string;
  endDate: string;
  onStartDateChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
};
