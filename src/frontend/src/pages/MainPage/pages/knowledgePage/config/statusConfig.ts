/** 状态配置条目 */
export interface StatusConfigEntry {
  label: string;
  textClass: string;
}

/** 知识库状态配置映射，包含标签和样式类名 */
export const STATUS_CONFIG: Record<string, StatusConfigEntry> = {
  ready: {
    label: "Ready",
    textClass: "text-accent-emerald-foreground",
  },
  ingesting: {
    label: "Ingesting",
    textClass: "text-accent-amber-foreground",
  },
  failed: {
    label: "Failed",
    textClass: "text-destructive",
  },
  cancelling: {
    label: "Cancelling",
    textClass: "text-accent-amber-foreground",
  },
  empty: {
    label: "Empty",
    textClass: "text-muted-foreground",
  },
};

/** 忙碌状态列表，这些状态下需要轮询更新 */
export const BUSY_STATUSES = ["ingesting", "cancelling"] as const;

/** 判断状态是否为忙碌状态 */
export const isBusyStatus = (status?: string): boolean =>
  BUSY_STATUSES.includes(status as (typeof BUSY_STATUSES)[number]);
