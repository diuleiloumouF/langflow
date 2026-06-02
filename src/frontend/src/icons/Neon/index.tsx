// Neon 图标组件 - 用于 Neon Serverless PostgreSQL 数据库相关组件的标识
import React, { forwardRef } from "react";
import NeonIconSVG from "./neon";

export const NeonIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <NeonIconSVG ref={ref} {...props} />;
  },
);
