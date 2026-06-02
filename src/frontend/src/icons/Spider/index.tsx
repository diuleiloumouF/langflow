// Spider 图标组件 - 用于 Spider 网页爬虫服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSpiderIcon from "./SpiderIcon";

export const SpiderIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgSpiderIcon ref={ref} {...props} />;
});
