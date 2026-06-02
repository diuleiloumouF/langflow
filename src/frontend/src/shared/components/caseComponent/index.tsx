import { memo } from "react";

// 类似布尔值的类型，可以是布尔、字符串、数字、null 或 undefined
type BooleanLike = boolean | string | number | null | undefined;

// Case 组件的属性类型
type Props = {
  // 条件值，可以是函数或直接的布尔类似值
  condition: (() => BooleanLike) | BooleanLike;
  // 条件为真时渲染的子元素
  children: React.ReactNode | any;
};

/**
 * Case 条件渲染组件
 * 根据条件判断是否渲染子元素，类似于条件表达式的组件封装
 */
export const Case = memo(({ condition, children }: Props) => {
  // 如果条件是函数则执行获取结果，否则直接使用
  const conditionResult =
    typeof condition === "function" ? condition() : condition;

  // 条件为真时渲染子元素，否则返回 null
  return conditionResult ? children : null;
});
