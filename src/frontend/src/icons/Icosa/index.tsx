// Icosa 图标组件 - 用于 Icosa 3D 模型服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgIcosa from "./Icosa";

export const IcosaIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgIcosa ref={ref} {...props} />;
  },
);
