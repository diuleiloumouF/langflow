import { useEffect } from "react";

/**
 * 滚动到元素 Hook
 * 根据元素 ID 平滑滚动到页面中的指定位置
 */
const useScrollToElement = (scrollId: string | null | undefined) => {
  useEffect(() => {
    const element = document.getElementById(scrollId ?? "null");
    if (element) {
      // Scroll smoothly to the top of the next section
      element.scrollIntoView({ behavior: "smooth" });
    }
  }, [scrollId]);
};

export default useScrollToElement;
