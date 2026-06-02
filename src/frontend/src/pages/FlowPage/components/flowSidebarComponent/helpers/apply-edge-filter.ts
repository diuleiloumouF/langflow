import type { APIDataType } from "@/types/api";

/**
 * 应用边筛选器
 * 根据组件族和类型筛选组件数据，用于按输出类型筛选可连接的组件
 */
export const applyEdgeFilter = (filteredData: APIDataType, getFilterEdge) => {
  return Object.fromEntries(
    Object.entries(filteredData).map(([family, familyData]) => {
      const edgeFilter = getFilterEdge.find((x) => x.family === family);
      if (!edgeFilter) return [family, {}];

      const filteredTypes = edgeFilter.type
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t !== "");

      if (filteredTypes.length === 0) return [family, familyData];

      const filteredFamilyData = Object.fromEntries(
        Object.entries(familyData).filter(([key]) =>
          filteredTypes.includes(key),
        ),
      );

      return [family, filteredFamilyData];
    }),
  );
};
