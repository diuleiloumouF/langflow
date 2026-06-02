import type { ReactNode } from "react";
import { cn } from "@/utils/utils";
import { BorderBeam } from "../../../components/ui/border-beams";

/** 增强光束效果组件的属性定义 */
interface EnhancedBeamEffectProps {
  children: ReactNode;
  className?: string;
  primaryColor?: string;
  secondaryColor?: string;
  size?: number;
}

/**
 * 增强光束效果组件
 * 为子元素添加动态光束边框效果，支持自定义颜色和大小
 */
export const EnhancedBeamEffect = ({
  children,
  className,
  primaryColor = "#C661B8",
  secondaryColor = "#61C6B8",
  size = 200,
}: EnhancedBeamEffectProps) => {
  return (
    <div
      className={cn(
        "relative flex items-center justify-center overflow-hidden rounded-xl",
        className,
      )}
    >
      {children}

      {/* Primary beam - larger, slower rotation */}
      <BorderBeam
        duration={12}
        size={size}
        className="opacity-80"
        colorFrom={primaryColor}
        colorTo={secondaryColor}
        anchor={20}
        borderWidth={1.5}
      />
    </div>
  );
};

export default EnhancedBeamEffect;
