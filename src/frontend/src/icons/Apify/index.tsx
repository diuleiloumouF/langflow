// Apify 图标组件 - 用于 Apify 网页爬虫和自动化平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgApifyLogo from "./Apify";
import ApifyWhiteImage from "./apify_white.png";

export const ApifyIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgApifyLogo ref={ref} {...props} />;
  },
);

// ApifyWhiteIcon: Apify 白色版本图标，用于深色背景
export const ApifyWhiteIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <img src={ApifyWhiteImage} alt="Apify White Logo" {...props} />;
});
