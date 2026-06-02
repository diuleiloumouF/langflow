// BotMessageSquare 图标组件 - 用于机器人消息界面相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgChroma from "./BotMessageSquare";

export const BotMessageSquareIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgChroma ref={ref} {...props} />;
});
