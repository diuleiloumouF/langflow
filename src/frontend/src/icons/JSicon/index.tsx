// JavaScript 图标组件 - 用于 JavaScript 编程语言相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgJSIcon from "./JSIcon";

export const JSIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgJSIcon ref={ref} {...props} />;
  },
);
