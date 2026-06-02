import { normalizeString } from "./normalize-string";

/**
 * 在元数据中搜索
 * 递归搜索组件的元数据对象，检查键或值是否匹配搜索词
 */
export function searchInMetadata(metadata: any, searchTerm: string): boolean {
  if (!metadata || typeof metadata !== "object") return false;

  return Object.entries(metadata).some(([key, value]) => {
    if (typeof value === "string") {
      return (
        normalizeString(key).includes(searchTerm) ||
        normalizeString(value).includes(searchTerm)
      );
    }
    if (typeof value === "object") {
      return searchInMetadata(value, searchTerm);
    }
    return false;
  });
}
