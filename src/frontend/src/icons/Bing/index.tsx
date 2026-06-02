// Bing 图标组件 - 用于 Bing 搜索服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgBing from "./Bing";

export const BingIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgBing ref={ref} {...props} />;
  },
);
