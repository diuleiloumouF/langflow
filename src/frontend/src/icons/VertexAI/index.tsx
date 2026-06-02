// Vertex AI 图标组件 - 用于 Google Vertex AI 机器学习平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgVertexAi from "./VertexAi";

export const VertexAIIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgVertexAi ref={ref} {...props} />;
});
