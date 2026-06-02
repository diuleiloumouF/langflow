import { toCamelCase, toTitleCase } from "@/utils/utils";

/** 快捷键项类型 */
type ShortcutItem = {
  name: string;
  shortcut: string;
  display_name: string;
};

/**
 * 根据名称查找快捷键
 * @param shortcuts - 快捷键列表
 * @param shortcutName - 快捷键名称
 * @returns 匹配的快捷键项，未找到返回 undefined
 */
export function findShortcutByName(
  shortcuts: ShortcutItem[],
  shortcutName: string,
): ShortcutItem | undefined {
  return shortcuts.find(
    (shortcut) =>
      toCamelCase(shortcut.name) === toCamelCase(shortcutName ?? ""),
  );
}

/**
 * 检查快捷键组合是否重复
 * 用于在编辑快捷键时检测冲突
 */
export function isDuplicateCombination(
  shortcuts: ShortcutItem[],
  currentName: string,
  newCombination: string,
): boolean {
  return shortcuts.some(
    (existing) =>
      existing.name !== currentName &&
      existing.shortcut.toLowerCase() === newCombination.toLowerCase(),
  );
}

/**
 * 获取修正后的快捷键组合
 * 将录制的按键组合规范化为标准格式
 */
export function getFixedCombination(
  oldKey: string | null,
  key: string,
): string {
  if (oldKey === null) {
    return `${key.length > 0 ? toTitleCase(key) : toTitleCase(key)}`;
  }
  return `${
    oldKey.length > 0 ? toTitleCase(oldKey) : oldKey.toUpperCase()
  } + ${key.length > 0 ? toTitleCase(key) : key.toUpperCase()}`;
}

/**
 * 检查按键是否匹配
 * 用于检测快捷键录制过程中的按键冲突
 */
export function checkForKeys(keys: string, keyToCompare: string): boolean {
  const keysArr = keys.split(" ");
  return keysArr.some(
    (k) => k.toLowerCase().trim() === keyToCompare.toLowerCase().trim(),
  );
}

/**
 * 标准化录制的快捷键组合
 * 将 Ctrl/Cmd 统一为 "mod"，并规范化格式
 */
export function normalizeRecordedCombination(recorded: string): string {
  const parts = recorded.split(" ");
  if (
    parts[0]?.toLowerCase().includes("ctrl") ||
    parts[0]?.toLowerCase().includes("cmd")
  ) {
    parts[0] = "mod";
  }
  return parts.join("").toLowerCase();
}
