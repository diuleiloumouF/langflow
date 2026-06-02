// AWS 图标组件 - 用于 Amazon Web Services 相关服务的标识
import React, { forwardRef } from "react";
import SvgAWS from "./AWS";

export const AWSIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgAWS ref={ref} {...props} />;
  },
);
