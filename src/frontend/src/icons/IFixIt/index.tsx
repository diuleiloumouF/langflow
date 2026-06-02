// IFixIt 图标组件 - 用于 IFixIt 维修指南平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgIfixitSeeklogocom from "./IfixitSeeklogoCom";

export const IFixIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgIfixitSeeklogocom ref={ref} {...props} />;
  },
);
