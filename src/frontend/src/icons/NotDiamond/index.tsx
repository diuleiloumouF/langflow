// NotDiamond 图标组件 - 用于 NotDiamond AI 模型路由优化服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgNotDiamondIcon from "./NotDiamondIcon";

export const NotDiamondIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgNotDiamondIcon ref={ref} {...props} />;
});
