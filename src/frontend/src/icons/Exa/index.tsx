// Exa 图标组件 - 用于 Exa 搜索引擎相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgExa from "./Exa";

export const ExaIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgExa ref={ref} {...props} />;
  },
);
