// Streamlit 图标组件 - 用于 Streamlit 数据应用框架相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgStreamlit from "./SvgStreamlit";

export const Streamlit = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgStreamlit className="icon" ref={ref} {...props} />;
  },
);
