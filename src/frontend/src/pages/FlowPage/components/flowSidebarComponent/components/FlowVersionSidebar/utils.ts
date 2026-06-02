/**
 * 格式化时间戳为可读的日期字符串
 * @param dateStr - ISO 格式的日期字符串
 * @returns 格式化后的日期字符串（如 "Jan 15, 2:30 PM"）
 */
export function formatTimestamp(dateStr: string): string {
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return "Unknown date";
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
