// YouTube 图标组件 - 用于 YouTube 视频平台相关组件的标识
import React, { forwardRef } from "react";
import YoutubeIconSVG from "./youtube";

export const YoutubeIcon = forwardRef<
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
      <YoutubeIconSVG ref={ref} {...props} />
    </span>
  );
});
