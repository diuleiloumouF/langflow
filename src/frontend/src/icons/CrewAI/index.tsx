// CrewAI 图标组件 - 用于 CrewAI 多智能体协作框架相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgCrewAiIcon from "./CrewAiIcon";

export const CrewAiIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgCrewAiIcon ref={ref} {...props} />;
});
