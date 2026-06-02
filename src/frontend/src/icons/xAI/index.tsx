// xAI 图标组件 - 用于 xAI (Elon Musk 的 AI 公司) 相关组件的标识
import React, { forwardRef } from "react";
import XAISVG from "./xAIIcon.jsx";

export const XAIIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <XAISVG ref={ref} {...props} />;
  },
);
