// GitHub Composio 图标组件 - 用于 GitHub 通过 Composio 集成的相关组件的标识
import React, { forwardRef } from "react";
import GithubIconSVG from "./github";

export const GithubIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <GithubIconSVG ref={ref} {...props} />;
});
