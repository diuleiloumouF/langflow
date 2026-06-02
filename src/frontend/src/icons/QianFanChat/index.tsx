// 千帆聊天 图标组件 - 用于百度千帆大模型平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgQianFanChat from "./QianFanChat";

export const QianFanChatIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgQianFanChat ref={ref} {...props} />;
});
