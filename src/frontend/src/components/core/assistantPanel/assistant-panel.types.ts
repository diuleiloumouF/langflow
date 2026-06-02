import type {
  AgenticProgressState,
  AgenticResult,
  AgenticStepType,
} from "@/controllers/API/queries/agentic";

/**
 * 助手消息类型定义
 * 包含消息状态、模型、建议、面板属性等类型定义
 */
export type AssistantMessageStatus =
  | "pending"
  | "streaming"
  | "complete"
  | "error"
  | "cancelled";

export interface AssistantMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  status?: AssistantMessageStatus;
  progress?: AgenticProgressState;
  completedSteps?: AgenticStepType[];
  result?: AgenticResult;
  error?: string;
}

export interface AssistantModel {
  id: string;
  name: string;
  provider: string;
  displayName: string;
}

export interface AssistantSuggestion {
  id: string;
  icon: string;
  text: string;
}

export interface AssistantPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

/** 序列化的助手消息，Date 类型转为 ISO 字符串，移除 progress 字段 */
export type SerializedAssistantMessage = Omit<
  AssistantMessage,
  "timestamp" | "progress"
> & {
  timestamp: string;
};

/** 保存在 localStorage 中的会话记录条目 */
export interface SessionHistoryEntry {
  sessionId: string;
  firstUserMessage: string;
  messageCount: number;
  lastActiveAt: string;
  messages: SerializedAssistantMessage[];
}
