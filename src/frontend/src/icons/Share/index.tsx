// Share 图标组件 - 用于分享功能相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgShare from "./Share";

export const ShareIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgShare ref={ref} {...props} />;
  },
);
