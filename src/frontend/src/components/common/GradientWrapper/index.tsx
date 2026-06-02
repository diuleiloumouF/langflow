import type { ReactNode } from "react";

/**
 * 渐变色包装器组件
 * 提供一个隐藏的 SVG 渐变定义，供子组件中的元素引用该渐变效果。
 * 渐变色包含粉色、紫色等渐变过渡色。
 */
export function GradientWrapper({ children }: { children: ReactNode }) {
  return (
    <>
      <svg width="0" height="0" className="absolute">
        <defs>
          <linearGradient id="x-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="-35.61%" stopColor="#e6b1e1" />
            <stop offset="13.03%" stopColor="#e94b71" />
            <stop offset="61.67%" stopColor="#b79bde" />
            <stop offset="126.52%" stopColor="#e955cb" />
          </linearGradient>
        </defs>
      </svg>
      {children}
    </>
  );
}
