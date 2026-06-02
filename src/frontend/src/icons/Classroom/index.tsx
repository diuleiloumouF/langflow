// Classroom 图标组件 - 用于 Google Classroom 教育平台相关组件的标识
import React, { forwardRef } from "react";
import ClassroomIconSVG from "./classroom";

export const ClassroomIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <ClassroomIconSVG ref={ref} {...props} />;
});
