// Google Sheets 图标组件 - 用于 Google Sheets 在线电子表格服务相关组件的标识
import React, { forwardRef } from "react";
import GooglesheetsIconSVG from "./googlesheets";

export const GooglesheetsIcon = forwardRef<
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
      <GooglesheetsIconSVG ref={ref} {...props} />
    </span>
  );
});
