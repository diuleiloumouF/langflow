// Google Meet 图标组件 - 用于 Google Meet 视频会议服务相关组件的标识
import React, { forwardRef } from "react";
import GooglemeetIconSVG from "./googlemeet";

export const GooglemeetIcon = forwardRef<
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
      <GooglemeetIconSVG ref={ref} {...props} />
    </span>
  );
});
