// GitHub 图标组件 - 用于 GitHub 代码托管平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import GithubIconSVG from "./github";

export const GithubIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <span
      style={{
        display: "inline-grid",
        width: 24,
        height: 24,
        placeItems: "center",
        flexShrink: 0,
      }}
    >
      <GithubIconSVG ref={ref} {...props} style={{ width: 22, height: 22 }} />
    </span>
  );
});
