// Bolna 图标组件 - 用于 Bolna AI 电话助手服务相关组件的标识
import React, { forwardRef } from "react";
import BolnaIconSVG from "./bolna";

export const BolnaIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <BolnaIconSVG ref={ref} {...props} />;
  },
);
