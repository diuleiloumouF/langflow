import { CustomNavigate } from "@/customization/components/custom-navigate";
import { useStoreStore } from "../../../stores/storeStore";

/**
 * 商店功能路由守卫组件
 * 保护需要商店功能才能访问的页面。
 * - 未启用商店功能时重定向到全部页面
 * - 已启用商店功能时正常渲染子组件
 */
export const StoreGuard = ({ children }) => {
  const hasStore = useStoreStore((state) => state.hasStore);

  if (!hasStore) {
    return <CustomNavigate to="/all" replace />;
  }

  return children;
};
