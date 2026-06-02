// Word 图标组件 - 用于 Microsoft Word 文档处理相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgWord from "./Word";

export const WordIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgWord ref={ref} {...props} />;
  },
);
