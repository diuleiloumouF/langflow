/** 部署提供商类型枚举 */
export type DeploymentProviderType = "watsonx" | "kubernetes";

/** 环境变量条目 */
export interface EnvVarEntry {
  id: string;
  key: string;
  value: string;
  globalVar?: boolean;
}

/** 连接项数据结构 */
export interface ConnectionItem {
  id: string;
  connectionId: string;
  name: string;
  environment?: string;
  variableCount: number;
  isNew: boolean;
  environmentVariables: Record<string, string>;
  globalVarKeys?: Set<string>;
}

/** 部署提供商配置 */
export interface DeploymentProvider {
  id: string;
  type: DeploymentProviderType;
  name: string;
  icon: string;
}

/** 提供商账户数据结构 */
export interface ProviderAccount {
  id: string;
  name: string;
  provider_key: string;
  provider_data?: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
}

/** 提供商凭据数据结构 */
export interface ProviderCredentials {
  name: string;
  provider_key: string;
  url: string;
  api_key: string;
}

export type DeploymentType = "agent" | "mcp";

export interface Deployment {
  id: string;
  provider_id?: string;
  name: string;
  description?: string;
  type: DeploymentType;
  created_at: string;
  updated_at: string;
  provider_data?: Record<string, unknown>;
  resource_key: string;
  attached_count: number;
  flow_version_ids?: string[];
}

export interface SnapshotUpdateResponse {
  flow_version_id: string;
  provider_snapshot_id: string;
}
