// OneDrive 图标组件 (备选样式) - 用于 Microsoft OneDrive 云存储服务相关组件的标识
import React, { forwardRef } from "react";
import One_DriveIconSVG from "./one_drive";

export const One_DriveIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <span
      style={{
        display: "inline-grid",
        width: 22,
        height: 22,
        placeItems: "center",
        flexShrink: 0,
      }}
    >
      <One_DriveIconSVG ref={ref} {...props} />
    </span>
  );
});
