import type { APIDataType } from "@/types/api";

/**
 * 应用 Legacy 筛选器
 * 从组件数据中过滤掉所有标记为 Legacy 的组件
 */
export const applyLegacyFilter = (filteredData: APIDataType) => {
  return Object.fromEntries(
    Object.entries(filteredData).map(([category, items]) => [
      category,
      Object.fromEntries(
        Object.entries(items).filter(([_, value]) => !value.legacy),
      ),
    ]),
  );
};
