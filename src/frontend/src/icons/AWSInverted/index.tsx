// AWS Inverted 图标组件 - 用于 AWS 反色样式图标相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgAWS from "./AWS";

export const AWSInvertedIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgAWS ref={ref} {...props} />;
});
