// Groq 图标组件 - 用于 Groq 高性能推理芯片服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgGroqLogo from "./GroqLogo";

export const GroqIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgGroqLogo ref={ref} {...props} />;
  },
);
