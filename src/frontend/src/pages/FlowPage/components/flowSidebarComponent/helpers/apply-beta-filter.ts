import type { APIDataType } from "@/types/api";

/**
 * 应用 Beta 筛选器
 * 从组件数据中过滤掉所有标记为 Beta 的组件
 */
export const applyBetaFilter = (filteredData: APIDataType) => {
  return Object.fromEntries(
    Object.entries(filteredData).map(([category, items]) => [
      category,
      Object.fromEntries(
        Object.entries(items).filter(([_, value]) => !value.beta),
      ),
    ]),
  );
};
