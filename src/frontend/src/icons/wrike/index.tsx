// Wrike 图标组件 - 用于 Wrike 项目管理平台相关组件的标识
import React, { forwardRef } from "react";
import WrikeIconSVG from "./wrike";

export const WrikeIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <WrikeIconSVG ref={ref} {...props} />;
  },
);
