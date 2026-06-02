// Searx 图标组件 - 用于 Searx 元搜索引擎相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSearxLogo from "./SearxLogo";

export const SearxIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgSearxLogo ref={ref} {...props} />;
  },
);
