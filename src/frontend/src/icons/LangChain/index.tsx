// LangChain 图标组件 - 用于 LangChain 框架相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgLangChainIcon from "./LangChainIcon";

export const LangChainIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgLangChainIcon ref={ref} {...props} />;
});
