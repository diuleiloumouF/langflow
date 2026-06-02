// vLLM 图标组件 - 用于 vLLM 高性能大语言模型推理引擎相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgVLLM from "./vLLM";

export const VllmIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgVLLM ref={ref} {...props} />;
  },
);
