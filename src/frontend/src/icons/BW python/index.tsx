// 黑白 Python 图标组件 - 用于 Python 编程语言的黑白样式标识
import type React from "react";
import { forwardRef } from "react";
import BWSvgPython from "./Python";

export const BWPythonIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <BWSvgPython ref={ref} {...props} />;
});
