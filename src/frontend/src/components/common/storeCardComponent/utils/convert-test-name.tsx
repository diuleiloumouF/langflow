/**
 * 转换测试名称
 * 将名称中的空格替换为连字符并转为小写，用于生成 data-testid 属性值。
 */
export function convertTestName(name: string): string {
  return name.replace(/ /g, "-").toLowerCase();
}
