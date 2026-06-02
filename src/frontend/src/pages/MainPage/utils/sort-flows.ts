/**
 * 排序流程列表
 * 根据类型筛选流程，并按更新时间降序排序
 */
export const sortFlows = (flows, type) => {
  const isComponent = type === "component";

  const sortByDateFn = (a, b) => {
    const dateA = a?.updated_at || a?.date_created;
    const dateB = b?.updated_at || b?.date_created;

    return sortByDate(dateA, dateB);
  };

  const filteredFlows =
    type === "all"
      ? flows
      : flows?.filter((f) => (f?.is_component ?? false) === isComponent);

  return filteredFlows?.sort(sortByDateFn) ?? [];
};

/**
 * 按日期排序
 * 降序排列，较新的日期排在前面
 */
export const sortByDate = (dateA: string, dateB: string) => {
  if (dateA && dateB) {
    return new Date(dateB).getTime() - new Date(dateA).getTime();
  } else if (dateA) {
    return 1;
  } else if (dateB) {
    return -1;
  } else {
    return 0;
  }
};

/**
 * 按布尔值排序
 * true 排在 false 前面
 */
export const sortByBoolean = (a: boolean, b: boolean) => {
  if (a && b) {
    return 0;
  } else if (a && !b) {
    return -1;
  } else if (!a && b) {
    return 1;
  } else {
    return 0;
  }
};
