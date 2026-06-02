// Glean 图标组件 - 用于 Glean 企业搜索平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgGlean from "./Glean";

export const GleanIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgGlean ref={ref} {...props} />;
  },
);
