import { useEffect, useRef, useState } from "react";

/**
 * 水平滚动渐隐组件
 * 为内容提供水平滚动功能，并在左右两侧显示渐隐效果。
 * 当内容可滚动时，左侧和右侧会显示渐变遮罩提示用户可以继续滚动。
 */
export default function HorizontalScrollFadeComponent({
  children,
  isFolder = true,
}: {
  children: JSX.Element | JSX.Element[];
  isFolder?: boolean;
}) {
  const scrollContainerRef = useRef<HTMLDivElement>(null); // 滚动容器引用
  const fadeContainerRef = useRef<HTMLDivElement>(null); // 渐隐容器引用
  const [divWidth, setDivWidth] = useState<number>(0); // 容器宽度

  // 监听窗口大小变化，更新容器宽度
  useEffect(() => {
    const handleResize = () => {
      if (scrollContainerRef.current) {
        setDivWidth(scrollContainerRef.current.clientWidth);
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize(); // call the function at start to get the initial width
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // 监听滚动事件，根据滚动位置显示/隐藏渐隐效果
  useEffect(() => {
    const handleScroll = () => {
      if (!scrollContainerRef.current || !fadeContainerRef.current) return;

      const { scrollLeft, scrollWidth, clientWidth } =
        scrollContainerRef.current;
      const atStart = scrollLeft === 0;
      const atEnd = scrollLeft === scrollWidth - clientWidth;
      const isScrollable = scrollWidth > clientWidth;

      fadeContainerRef.current.classList.toggle(
        "fade-left",
        isScrollable && !atStart,
      );
      fadeContainerRef.current.classList.toggle(
        "fade-right",
        isScrollable && !atEnd,
      );
    };

    const scrollContainer = scrollContainerRef.current;
    if (scrollContainer) {
      scrollContainer.addEventListener("scroll", handleScroll);
      // Delay the initial scroll event dispatch to ensure correct calculation
      scrollContainer.dispatchEvent(new Event("scroll"));
      return () => scrollContainer.removeEventListener("scroll", handleScroll);
    }
  }, [divWidth, children]); // Depend on divWidth

  return isFolder ? (
    <div className="flex w-full flex-col gap-2">{children}</div>
  ) : (
    <div ref={fadeContainerRef} className="fade-container flex">
      <div ref={scrollContainerRef} className="scroll-container flex gap-2">
        {children}
      </div>
    </div>
  );
}
