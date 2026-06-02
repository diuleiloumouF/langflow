import { useEffect, useState } from "react";

/**
 * 加载文字组件
 * 显示带有动态省略号动画的加载文字。
 * 省略号会以 300ms 的间隔循环显示（. -> .. -> ... -> 空）。
 */
const LoadingTextComponent = ({ text }: { text: string }) => {
  const [dots, setDots] = useState(".");

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prevDots) => (prevDots === "..." ? "" : `${prevDots}.`));
    }, 300);

    return () => {
      clearInterval(interval);
    };
  }, []);

  if (!text) {
    return null;
  }

  return <span>{`${text}${dots}`}</span>;
};

export default LoadingTextComponent;
