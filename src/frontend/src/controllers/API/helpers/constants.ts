/**
 * API 常量模块
 * 定义所有 API 端点的 URL 路径
 */
import { getBaseUrl } from "@/customization/utils/urls";
import { BASE_URL_API_V2 } from "../../../constants/constants";

/**
 * API 端点 URL 常量
 * 包含所有后端 API 的路径定义
 */
export const URLs = {
  TRANSACTIONS: `monitor/transactions`,
  TRACES: `monitor/traces`,
  API_KEY: `api_key`,
  FILES: `files`,
  FILE_MANAGEMENT: `files`,
  VERSION: `version`,
  MESSAGES: `monitor/messages`,
  BUILDS: `monitor/builds`,
  STORE: `store`,
  USERS: "users",
  LOGOUT: `logout`,
  LOGIN: `login`,
  SESSION: `session`,
  AUTOLOGIN: "auto_login",
  REFRESH: "refresh",
  BUILD: `build`,
  CUSTOM_COMPONENT: `custom_component`,
  FLOWS: `flows`,
  FOLDERS: `projects`,
  PROJECTS: `projects`,
  VARIABLES: `variables`,
  VALIDATE: `validate`,
  CONFIG: `config`,
  STARTER_PROJECTS: `starter-projects`,
  SIDEBAR_CATEGORIES: `sidebar_categories`,
  ALL: `all`,
  VOICE: `voice`,
  PUBLIC_FLOW: `flows/public_flow`,
  MCP: `mcp/project`,
  MCP_SERVERS: `mcp/servers`,
  KNOWLEDGE_BASES: `knowledge_bases`,
  MODELS: `models`,
  MODEL_PROVIDERS: `models/providers`,
  RUN: `run`,
  RUN_SESSION: `run/session`,
  REGISTRATION: `registration`,
  DEPLOYMENTS: `deployments`,
  DEPLOYMENT_PROVIDER_ACCOUNTS: `deployments/providers`,
  AGENTIC_ASSIST: `agentic/assist`,
  AGENTIC_ASSIST_STREAM: `agentic/assist/stream`,
  AGENTIC_CHECK_CONFIG: `agentic/check-config`,
} as const;

// 重要：FOLDERS 端点现在指向 'projects' 以保持向后兼容性

/**
 * 根据键名生成完整的 API URL
 * @param key - URL 键名
 * @param params - 可选的路径参数
 * @param v2 - 是否使用 V2 API 版本
 * @returns 完整的 API URL
 */
export function getURL(
  key: keyof typeof URLs,
  params: Record<string, unknown> = {},
  v2: boolean = false,
) {
  let url = URLs[key];
  for (const paramKey of Object.keys(params)) {
    url += `/${params[paramKey]}`;
  }
  return `${v2 ? BASE_URL_API_V2 : getBaseUrl()}${url}`;
}

// URL 常量的类型定义
export type URLsType = typeof URLs;
