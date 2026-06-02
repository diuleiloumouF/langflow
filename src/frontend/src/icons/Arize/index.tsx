// Arize 图标组件 - 用于 Arize AI 可观测性平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgArize from "./Arize";

export const ArizeIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgArize ref={ref} {...props} />;
  },
);
