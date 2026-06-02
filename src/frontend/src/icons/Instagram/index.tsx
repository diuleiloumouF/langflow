// Instagram 图标组件 - 用于 Instagram 社交媒体平台相关组件的标识
import React, { forwardRef } from "react";
import InstagramIconSVG from "./instagram";

export const InstagramIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <InstagramIconSVG ref={ref} {...props} />;
});
