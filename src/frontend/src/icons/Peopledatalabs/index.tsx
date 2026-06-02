// People Data Labs 图标组件 - 用于 People Data Labs 人员数据 API 服务相关组件的标识
import React, { forwardRef } from "react";
import PeopledatalabsIconSVG from "./peopledatalabs";

export const PeopledatalabsIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <PeopledatalabsIconSVG
      ref={ref}
      {...props}
      style={{ width: 20, height: 20 }}
    />
  );
});
