// Azure Logo 图标组件 - 用于 Azure 云服务品牌标识相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgAzLogo from "./AzLogo";

export const AzIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgAzLogo ref={ref} {...props} />;
  },
);
