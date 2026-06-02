// Azure 图标组件 - 用于 Microsoft Azure 云服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgAzure from "./Azure";

export const AzureIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgAzure ref={ref} {...props} />;
  },
);
