// Thumbs 图标组件集合 - 用于用户反馈（点赞/点踩）相关组件的标识
// ThumbUpIconCustom: 自定义点赞图标
import type React from "react";
import { forwardRef } from "react";
import ThumbDownFilled from "./thumbDown";
import ThumbUpFilled from "./thumbUp";

export const ThumbUpIconCustom = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <ThumbUpFilled ref={ref} {...props} />;
});

// ThumbDownIconCustom: 自定义点踩图标
export const ThumbDownIconCustom = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <ThumbDownFilled ref={ref} {...props} />;
});
