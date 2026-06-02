// Snowflake 图标组件 - 用于 Snowflake 云数据平台相关组件的标识
import React, { forwardRef } from "react";
import SnowflakeIconSVG from "./snowflake";

export const SnowflakeIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <SnowflakeIconSVG ref={ref} {...props} style={{ width: 20, height: 20 }} />
  );
});
