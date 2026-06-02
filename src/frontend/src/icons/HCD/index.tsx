// HCD 图标组件 - 用于 HCD (人机协作) 相关组件的标识
import React, { forwardRef } from "react";
import HCDSVG from "./HCD";

export const HCDIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <HCDSVG ref={ref} {...props} />;
  },
);
