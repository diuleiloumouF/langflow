import LoadingComponent from "@/components/common/loadingComponent";
import { cn } from "@/utils/utils";

/**
 * 加载页面组件
 * 全屏居中显示加载动画
 * @param overlay - 是否作为覆盖层显示（fixed 定位，最高层级）
 */
export function LoadingPage({ overlay = false }: { overlay?: boolean }) {
  return (
    <div
      className={cn(
        "flex h-screen w-screen items-center justify-center bg-background",
        overlay && "fixed left-0 top-0 z-[999]",
      )}
    >
      <LoadingComponent remSize={50} />
    </div>
  );
}
