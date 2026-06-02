// Google Maps 图标组件 - 用于 Google Maps 地图服务相关组件的标识
import React, { forwardRef } from "react";
import GooglemapsIconSVG from "./googlemaps";

export const GooglemapsIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <GooglemapsIconSVG ref={ref} {...props} />;
});
