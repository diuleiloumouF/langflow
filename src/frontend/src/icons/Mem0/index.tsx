// Mem0 图标组件 - 用于 Mem0 AI 记忆管理服务相关组件的标识
import React, { forwardRef } from "react";
import SvgMem from "./SvgMem";

export const Mem0 = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgMem className="icon" ref={ref} {...props} />;
  },
);
