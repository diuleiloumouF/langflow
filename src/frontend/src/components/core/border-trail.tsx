import { motion, type Transition } from "framer-motion";
import { cn } from "@/utils/utils";

/**
 * 边框拖尾动画组件
 * 在元素边框上创建一个沿着路径移动的光效动画。
 * 使用 framer-motion 的 offset-path 实现路径动画。
 */
type BorderTrailProps = {
  className?: string;
  size?: number | string;
  transition?: Transition;
  delay?: number;
  onAnimationComplete?: () => void;
  style?: React.CSSProperties;
};

export function BorderTrail({
  className,
  size = 60,
  transition,
  delay,
  onAnimationComplete,
  style,
}: BorderTrailProps) {
  const BASE_TRANSITION = {
    repeat: Infinity,
    duration: 5,
    ease: "linear",
  };

  return (
    <div className="pointer-events-none absolute inset-0 rounded-[inherit] border border-transparent [mask-clip:padding-box,border-box] [mask-composite:intersect] [mask-image:linear-gradient(transparent,transparent),linear-gradient(#000,#000)]">
      <motion.div
        className={cn("absolute bg-muted-foreground", className)}
        style={{
          width: size,
          offsetPath: `rect(0 auto auto 0 round 18px)`,
          boxShadow:
            "0px 0px 20px 5px rgb(255 255 255 / 90%), 0 0 30px 10px rgb(0 0 0 / 90%)",
          ...style,
        }}
        animate={{
          offsetDistance: ["0%", "100%"],
        }}
        transition={{
          ...(transition ?? BASE_TRANSITION),
          delay: delay,
        }}
        onAnimationComplete={onAnimationComplete}
      />
    </div>
  );
}
