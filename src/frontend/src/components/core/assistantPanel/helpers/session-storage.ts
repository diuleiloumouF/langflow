/**
 * 助手会话的序列化和反序列化工具
 * 用于将会话数据存储到 localStorage 和从 localStorage 加载。
 */
// Serialization and deserialization of assistant sessions for localStorage.

import type {
  AssistantMessage,
  SerializedAssistantMessage,
  SessionHistoryEntry,
} from "../assistant-panel.types";

// 从 localStorage 加载会话列表
export function loadSessionsFromStorage(
  storageKey: string,
): SessionHistoryEntry[] {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed;
  } catch {
    return [];
  }
}

// 保存会话列表到 localStorage
export function saveSessionsToStorage(
  storageKey: string,
  sessions: SessionHistoryEntry[],
): void {
  try {
    localStorage.setItem(storageKey, JSON.stringify(sessions));
  } catch {
    // localStorage may be full or unavailable
  }
}

// 将消息数组序列化为可存储的格式
export function serializeMessages(
  messages: AssistantMessage[],
): SerializedAssistantMessage[] {
  return messages.map((msg) => {
    const { timestamp, progress, result, ...rest } = msg;
    const serialized: SerializedAssistantMessage = {
      ...rest,
      timestamp: timestamp.toISOString(),
      // Streaming/pending messages become cancelled when session is saved
      status:
        msg.status === "streaming" || msg.status === "pending"
          ? "cancelled"
          : msg.status,
    };
    if (result) {
      serialized.result = result;
    }
    return serialized;
  });
}

// 将序列化的消息数组反序列化为 AssistantMessage 格式
export function deserializeMessages(
  serialized: SerializedAssistantMessage[],
): AssistantMessage[] {
  return serialized.map((msg) => ({
    ...msg,
    timestamp: new Date(msg.timestamp),
  }));
}
