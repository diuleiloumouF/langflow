// Python 图标组件 - 用于 Python 编程语言相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgPython from "./Python";

export const PythonIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgPython ref={ref} {...props} />;
});
