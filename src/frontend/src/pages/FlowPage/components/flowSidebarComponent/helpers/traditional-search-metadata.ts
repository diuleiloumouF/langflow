import type { APIDataType } from "@/types/api";
import { searchInMetadata } from "./search-on-metadata";

/**
 * 传统元数据搜索
 * 在组件的元数据中执行搜索，返回匹配的组件数据
 */
export const traditionalSearchMetadata = (
  data: APIDataType,
  searchTerm: string,
) => {
  return Object.fromEntries(
    Object.entries(data).map(([category, items]) => {
      const filteredItems = Object.fromEntries(
        Object.entries(items).filter(
          ([key, item]) =>
            item.metadata && searchInMetadata(item.metadata, searchTerm),
        ),
      );
      return [category, filteredItems];
    }),
  );
};
