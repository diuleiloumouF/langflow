// Meta 图标组件 - 用于 Meta (Facebook) 相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgMetaIcon from "./MetaIcon";

export const MetaIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgMetaIcon ref={ref} {...props} />;
  },
);
