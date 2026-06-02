// Hacker News 图标组件 - 用于 Hacker News 技术社区相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgYCombinatorLogo from "./YCombinatorLogo";

export const HackerNewsIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgYCombinatorLogo ref={ref} {...props} />;
});
