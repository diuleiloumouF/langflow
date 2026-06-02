// Google Drive 图标组件 - 用于 Google Drive 云存储服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgGoogleDrive from "./GoogleDrive";

export const GoogleDriveIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgGoogleDrive ref={ref} {...props} />;
});
