import type { FuseResult } from "fuse.js";
import type { APIDataType } from "@/types/api";

/**
 * 合并搜索结果函数
 * 将 Fuse.js 的模糊搜索结果按分类整理为与原始数据格式一致的对象
 */
export const combinedResultsFn = (
  fuseResults: FuseResult<any>[],
  data: APIDataType,
) => {
  return Object.fromEntries(
    Object.entries(data).map(([category]) => {
      const categoryResults = fuseResults.filter(
        (result) => result.item.category === category,
      );
      const filteredItems = Object.fromEntries(
        categoryResults.map((result) => [result.item.key, result.item]),
      );
      return [category, filteredItems];
    }),
  );
};
