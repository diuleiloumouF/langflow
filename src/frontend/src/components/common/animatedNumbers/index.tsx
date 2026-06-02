import {
  motion,
  type SpringOptions,
  useSpring,
  useTransform,
} from "framer-motion";
import { useEffect, useState } from "react";
import { cn } from "@/utils/utils";

/**
 * 动画数字属性类型
 * 定义 AnimatedNumber 组件的属性接口
 */
type AnimatedNumberProps = {
  value: number;
  humanizedValue?: string;
  className?: string;
  springOptions?: SpringOptions;
};

/**
 * 动画数字组件
 * 使用 framer-motion 的弹簧动画实现数字的平滑过渡效果。
 * 数字变化时会从旧值动画过渡到新值。
 */
export function AnimatedNumber({
  value,
  humanizedValue,
  className,
  springOptions,
}: AnimatedNumberProps) {
  // 创建弹簧动画，用于数字值的平滑过渡
  const spring = useSpring(value, springOptions);
  // 将弹簧动画值转换为带千位分隔符的格式化字符串
  const display = useTransform(spring, (current) =>
    Math.round(current).toLocaleString(),
  );

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  return (
    <motion.span className={cn("tabular-nums", className)}>
      {humanizedValue ?? display}
    </motion.span>
  );
}

/**
 * 基础动画数字示例组件
 * 展示 AnimatedNumber 的基本用法，数字从0动画到2082
 */
export function AnimatedNumberBasic() {
  const [value, setValue] = useState(0);

  useEffect(() => {
    setValue(2082);
  }, []);

  return (
    <div className="flex w-full items-center justify-center">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        width="16"
        height="16"
        className="mr-3 h-3 w-3 fill-transparent stroke-foreground stroke-[1.3]"
      >
        <path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"></path>
      </svg>
      <AnimatedNumber
        className="inline-flex items-center font-mono text-2xl font-light text-foreground"
        springOptions={{
          bounce: 0,
          duration: 2000,
        }}
        value={value}
      />
    </div>
  );
}
