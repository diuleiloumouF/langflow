import type { AssistantSuggestion } from "./assistant-panel.types";

// 助手面板标题
export const ASSISTANT_TITLE = "Langflow Assistant";

// 会话存储键前缀
export const ASSISTANT_SESSION_STORAGE_KEY_PREFIX =
  "langflow-assistant-session-";

// 助手输入框占位符文本列表
export const ASSISTANT_PLACEHOLDERS = [
  "Create an agent component...",
  "Build a RAG pipeline...",
  "Create a web scraper component...",
  "Build a document parser...",
  "Ask me anything about Langflow...",
];

// 随机获取一个占位符文本
export function getAssistantPlaceholder(): string {
  return ASSISTANT_PLACEHOLDERS[
    Math.floor(Math.random() * ASSISTANT_PLACEHOLDERS.length)
  ];
}

// 会话列表本地存储键
export const ASSISTANT_SESSIONS_STORAGE_KEY = "langflow-assistant-sessions";
// 最大保存会话数
export const ASSISTANT_MAX_SESSIONS = 10;
// 会话预览文本最大长度
export const ASSISTANT_SESSION_PREVIEW_LENGTH = 80;

// 助手欢迎文字
export const ASSISTANT_WELCOME_TEXT = "Here's how I can help";

// 助手建议操作列表
export const ASSISTANT_SUGGESTIONS: AssistantSuggestion[] = [
  {
    id: "build-agents",
    icon: "Sparkles",
    text: "Build agents and other components",
  },
  {
    id: "answer-questions",
    icon: "Sparkles",
    text: "Answer questions about Langflow",
  },
];
