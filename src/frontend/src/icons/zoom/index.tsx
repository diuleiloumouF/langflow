// Zoom 图标组件 - 用于 Zoom 视频会议服务相关组件的标识
import React, { forwardRef } from "react";
import ZoomIconSVG from "./zoom";

export const ZoomIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <ZoomIconSVG ref={ref} {...props} />;
  },
);
