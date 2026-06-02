// HuggingFace 图标组件 - 用于 HuggingFace AI 模型平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgHfLogo from "./HfLogo";

export const HuggingFaceIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgHfLogo ref={ref} {...props} />;
});
