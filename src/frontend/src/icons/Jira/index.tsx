// Jira 图标组件 - 用于 Jira 项目管理工具相关组件的标识
import React, { forwardRef } from "react";
import JiraIconSVG from "./jira";

export const JiraIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <JiraIconSVG ref={ref} {...props} />;
  },
);
