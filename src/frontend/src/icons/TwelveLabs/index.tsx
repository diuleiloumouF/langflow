// Twelve Labs 图标组件 - 用于 Twelve Labs 视频理解 AI 服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgTwelveLogo from "./TwelveLabsLogo";

export const TwelveLabsIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgTwelveLogo ref={ref} {...props} />;
});
