// Timelines AI 图标组件 - 用于 Timelines AI 项目管理服务相关组件的标识
import React, { forwardRef } from "react";
import TimelinesaiIconSVG from "./timelinesai";

export const TimelinesaiIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <TimelinesaiIconSVG ref={ref} {...props} />;
});
