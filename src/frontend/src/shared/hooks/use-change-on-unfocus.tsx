import { type RefObject, useEffect } from "react";

/**
 * useChangeOnUnfocus Hook 的属性接口
 * 当元素失去焦点或页面不可见时重置值
 */
interface UseChangeOnUnfocusProps<T> {
  // 是否处于选中状态
  selected?: boolean;
  // 当前值
  value: T;
  // 值变化时的回调函数
  onChange?: (value: T) => void;
  // 默认值（用于重置）
  defaultValue: T;
  // 判断是否应该更改值的条件函数
  shouldChangeValue?: (value: T) => boolean;
  // DOM 节点引用
  nodeRef: RefObject<HTMLDivElement | null>;
  // 值重置后的回调函数
  callback?: () => void;
  // ESC 键按下时的回调函数（已声明但未使用）
  callbackEscape?: () => void;
}

/**
 * useChangeOnUnfocus Hook
 * 在元素未选中或页面标签页不可见时，将值重置为默认值
 * 常用于输入框失去焦点后自动恢复原始值
 */
export function useChangeOnUnfocus<T>({
  selected,
  value,
  onChange,
  defaultValue,
  shouldChangeValue,
  nodeRef,
  callback,
}: UseChangeOnUnfocusProps<T>) {
  useEffect(() => {
    // 当未选中时，立即重置为默认值
    if (!selected) {
      onChange?.(defaultValue);
    }

    /**
     * 处理页面可见性变化
     * 当页面隐藏（切换标签页）且满足条件时，重置值
     */
    const handleVisibilityChange = () => {
      if (document.hidden && shouldChangeValue?.(value)) {
        onChange?.(defaultValue);
        callback?.();
      }
    };

    // 监听页面可见性变化事件
    document.addEventListener("visibilitychange", handleVisibilityChange);

    // 清理事件监听器
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [
    selected,
    value,
    onChange,
    defaultValue,
    shouldChangeValue,
    nodeRef,
    callback,
  ]);
}
