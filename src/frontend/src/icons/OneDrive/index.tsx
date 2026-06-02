// OneDrive 图标组件 - 用于 Microsoft OneDrive 云存储服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgOneDrive from "./OneDrive";

export const OneDriveIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgOneDrive ref={ref} {...props} />;
});
