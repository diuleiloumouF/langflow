// Google Docs 图标组件 - 用于 Google Docs 在线文档协作平台相关组件的标识
import React, { forwardRef } from "react";
import GoogledocsIconSVG from "./googledocs";

export const GoogledocsIcon = forwardRef<
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
      <GoogledocsIconSVG ref={ref} {...props} />
    </span>
  );
});
