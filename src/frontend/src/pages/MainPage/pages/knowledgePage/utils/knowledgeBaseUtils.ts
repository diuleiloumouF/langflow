/**
 * 格式化数字（添加千位分隔符）
 * Helper function to format numbers with commas
 */
export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num);
};

/**
 * 格式化平均分块大小
 * Format average chunk size with units
 */
export const formatAverageChunkSize = (avgChunkSize: number): string => {
  return `${formatNumber(Math.round(avgChunkSize))}`;
};
