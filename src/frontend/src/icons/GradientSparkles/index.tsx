// GradientSparkles 图标组件 - 包含渐变效果的工具图标集合
// GradientInfinity: 渐变无限符号图标，用于代码相关操作
import { Code } from "lucide-react";
import { forwardRef } from "react";
import ForwardedIconComponent from "../../components/common/genericIconComponent";

export const GradientInfinity = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <>
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <defs>
          <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop className="gradient-start" offset="0%" />
            <stop className="gradient-end" offset="100%" />
          </linearGradient>
        </defs>
      </svg>
      <Code stroke="url(#grad1)" ref={ref} {...props} />
    </>
  );
});

// GradientSave: 渐变保存图标，用于保存操作
export const GradientSave = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <>
      <ForwardedIconComponent
        name="Save"
        stroke="url(#x-gradient)"
        ref={ref}
        {...props}
      />
    </>
  );
});

// GradientGroup: 渐变分组图标，用于组合操作
export const GradientGroup = (props) => {
  return (
    <>
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <defs>
          <linearGradient id="grad3" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop className="gradient-start" offset="0%" />
            <stop className="gradient-end" offset="100%" />
          </linearGradient>
        </defs>
      </svg>
      <ForwardedIconComponent
        name="Combine"
        stroke={`${props.disabled ? "#64748B" : "url(#grad3)"}`}
        {...props}
      />
    </>
  );
};

// GradientUngroup: 渐变取消分组图标，用于取消组合操作
export const GradientUngroup = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <>
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <defs>
          <linearGradient id="grad4" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop className="gradient-start" offset="0%" />
            <stop className="gradient-end" offset="100%" />
          </linearGradient>
        </defs>
      </svg>
      <ForwardedIconComponent
        name="Ungroup"
        stroke="url(#grad4)"
        ref={ref}
        {...props}
      />
    </>
  );
});
