// Ollama 图标组件 - 用于 Ollama 本地大语言模型运行平台相关组件的标识
import React, { forwardRef } from "react";
import SvgOllama from "./Ollama";

export const OllamaIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgOllama ref={ref} {...props} />;
});
