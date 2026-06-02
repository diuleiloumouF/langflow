import type { APIDataType } from "@/types/api";

/**
 * 合并筛选数据函数
 * 将 Fuse.js 搜索结果和传统元数据搜索结果合并为统一的筛选数据
 */
export const filteredDataFn = (
  data: APIDataType,
  combinedResults,
  traditionalResults,
) => {
  return Object.fromEntries(
    Object.entries(data).map(([category, _]) => {
      const fuseItems = combinedResults[category] || {};
      const traditionalItems = traditionalResults[category] || {};

      const mergedItems = {
        ...fuseItems,
        ...traditionalItems,
      };

      return [category, mergedItems];
    }),
  );
};
