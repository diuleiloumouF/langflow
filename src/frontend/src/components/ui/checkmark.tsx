import { AnimatePresence, motion } from "framer-motion";
/**
 * 对勾动画组件
 * 使用 framer-motion 实现 SVG 对勾路径的绘制动画。
 * 支持初始动画和显示/隐藏过渡效果。
 */
export default function Checkmark({ initial = true, isVisible, className }) {
  return (
    <AnimatePresence initial={initial}>
      {isVisible && (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
          className={"CheckIcon " + className}
        >
          <motion.path
            initial={{ pathLength: 0, pathOffset: 1 }}
            animate={{ pathLength: 1, pathOffset: 0 }}
            exit={{ pathLength: 0, pathOffset: 1 }}
            transition={{
              type: "tween",
              duration: 0.3,
              ease: isVisible ? "easeOut" : "easeIn",
            }}
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M20 6 9 17l-5-5"
          />
        </svg>
      )}
    </AnimatePresence>
  );
}
