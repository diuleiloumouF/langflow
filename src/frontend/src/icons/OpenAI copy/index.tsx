// OpenAI 备选图标组件 - 用于 OpenAI 服务的备选样式标识
import React, { forwardRef } from "react";
import OpenAIIconSVG from "./openai";

export const OpenAIIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <OpenAIIconSVG ref={ref} {...props} />;
});
