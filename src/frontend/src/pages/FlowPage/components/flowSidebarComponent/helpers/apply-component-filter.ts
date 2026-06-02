import type { APIDataType } from "@/types/api";

/**
 * 应用组件筛选器
 * 根据指定的组件名称和分类筛选组件数据
 * @param filteredData - 待筛选的组件数据
 * @param getFilterComponent - 筛选条件，格式为 "分类.组件名"
 */
export const applyComponentFilter = (
  filteredData: APIDataType,
  getFilterComponent,
) => {
  const [category, component] = getFilterComponent.split(".");
  return Object.fromEntries(
    Object.entries(filteredData).map(([cat, items]) => [
      cat,
      Object.fromEntries(
        Object.entries(items).filter(
          ([name, _]) => name === component && cat === category,
        ),
      ),
    ]),
  );
};
