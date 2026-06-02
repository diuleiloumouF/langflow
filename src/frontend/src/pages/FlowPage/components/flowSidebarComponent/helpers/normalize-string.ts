/**
 * 标准化字符串
 * 将字符串转换为小写，替换下划线为空格，并移除所有空格
 * 用于搜索时的字符串比较
 */
export function normalizeString(str: string): string {
  return str.toLowerCase().replace(/_/g, " ").replace(/\s+/g, "");
}
