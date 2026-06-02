import { ADJECTIVES, NOUNS } from "../../../../../flow_constants";
import { getRandomElement } from "../../../../../utils/reactflowUtils";
import { toTitleCase } from "../../../../../utils/utils";

/**
 * 生成随机名称
 * 从预定义的形容词和名词列表中随机组合生成名称
 * @param retry - 当前重试次数，用于避免生成不合适的名称
 * @param noSpace - 是否不使用空格分隔（使用下划线代替）
 * @param maxRetries - 最大重试次数
 * @returns 标题格式的随机名称
 */
export default function getRandomName(
  retry: number = 0,
  noSpace: boolean = false,
  maxRetries: number = 3,
): string {
  const left: string[] = ADJECTIVES;
  const right: string[] = NOUNS;

  const lv = getRandomElement(left);
  const rv = getRandomElement(right);

  // Condition to avoid "boring wozniak"
  if (lv === "boring" && rv === "wozniak") {
    if (retry < maxRetries) {
      return getRandomName(retry + 1, noSpace, maxRetries);
    } else {
      console.warn("Max retries reached, returning as is");
    }
  }

  // Append a suffix if retrying and noSpace is true
  if (retry > 0 && noSpace) {
    const retrySuffix = Math.floor(Math.random() * 10);
    return `${lv}_${rv}${retrySuffix}`;
  }

  // Construct the final name
  const final_name = noSpace ? `${lv}_${rv}` : `${lv} ${rv}`;
  // Return title case final name
  return toTitleCase(final_name);
}
