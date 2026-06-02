/** 构建状态容器的动画变体 */
export const CONTAINER_VARIANTS = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 20 },
};

/** 停止按钮的动画变体 */
export const STOP_BUTTON_VARIANTS = {
  hidden: { opacity: 0, x: 0 },
  visible: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 0 },
};

/** 重试按钮的动画变体 */
export const RETRY_BUTTON_VARIANTS = {
  hidden: { opacity: 0, x: 10 },
  visible: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 10 },
};

/** 关闭按钮的动画变体 */
export const DISMISS_BUTTON_VARIANTS = {
  hidden: { opacity: 0, x: 10 },
  visible: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 10 },
};

/**
 * 获取时间显示的动画变体
 * 根据按钮宽度计算时间文本的位置偏移
 */
export const getTimeVariants = (buttonRef: React.RefObject<HTMLDivElement>) => {
  const errorButtonsWidth = buttonRef.current?.offsetWidth ?? 0;
  return {
    single: { x: 0, width: "auto" },
    double: { x: -errorButtonsWidth - 15, width: "auto" },
  };
};
