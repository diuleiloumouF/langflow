// AIML 图标组件 - 用于 AI/ML 相关服务和组件的标识
import type React from "react";
import { forwardRef } from "react";
import { AIMLComponent } from "./AI-ML";

export const AIMLIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{ className?: string }>
>((props, ref) => {
  return <AIMLComponent ref={ref} {...props} />;
});
