import { Skeleton } from "../../ui/skeleton";

/**
 * 骨架卡片组件
 * 在数据加载时显示的占位卡片，模拟卡片的头部和内容区域布局。
 */
export const SkeletonCardComponent = (): JSX.Element => {
  return (
    <div className="skeleton-card">
      <div className="skeleton-card-wrapper">
        <Skeleton className="h-8 w-8 rounded-full" />
        <Skeleton className="h-4 w-[40%]" />
      </div>
      <div className="skeleton-card-text">
        <Skeleton className="h-3 w-[90%]" />
        <Skeleton className="h-3 w-[80%]" />
      </div>
    </div>
  );
};
