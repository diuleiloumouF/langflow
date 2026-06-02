// Fixer 图标组件 - 用于 Fixer 汇率数据 API 服务相关组件的标识
import React, { forwardRef } from "react";
import FixerIconSVG from "./fixer";

export const FixerIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <FixerIconSVG ref={ref} {...props} />;
  },
);
