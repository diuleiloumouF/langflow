import { useCallback, useState } from "react";

/**
 * useAlternate 布尔值切换 Hook
 * 提供布尔值的状态管理，支持切换和直接设置两种操作
 * @param initialState - 初始状态，默认为 false
 * @returns [当前状态, 切换函数, 设置函数]
 */
export const useAlternate = (
  initialState: boolean = false,
): [boolean, () => void, (value: boolean) => void] => {
  // 管理布尔状态
  const [switched, setSwitched] = useState(initialState);
  // 直接设置状态值
  const set = useCallback((value) => setSwitched(value), []);

  // 切换状态（取反）
  const alternate = useCallback(
    () => setSwitched((prevState) => !prevState),
    [],
  );
  return [switched, alternate, set];
};
