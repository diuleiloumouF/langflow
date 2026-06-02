// Slack 图标组件 - 用于 Slack 团队协作通讯平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSlackIcon from "./SlackIcon";

export const SlackIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgSlackIcon ref={ref} {...props} />;
  },
);
