// Wolfram 图标组件 - 用于 Wolfram 计算知识引擎相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgWolfram from "./Wolfram";

export const WolframIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgWolfram ref={ref} {...props} />;
});
