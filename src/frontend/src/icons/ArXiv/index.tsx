// ArXiv 图标组件 - 用于 ArXiv 学术论文预印本平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgArXivIcon from "./ArXivIcon";

export const ArXivIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgArXivIcon ref={ref} {...props} />;
  },
);

export default ArXivIcon;
