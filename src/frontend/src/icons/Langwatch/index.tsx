// Langwatch 图标组件 - 用于 Langwatch LLM 可观测性平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgLangwatch from "./langwatch";

export const LangwatchIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgLangwatch ref={ref} {...props} />;
});
