import { useEffect } from "react";
import type { storeComponent } from "../../../../types/store";

/**
 * 数据效果 Hook
 * 当商店组件数据变化时，同步更新点赞状态、点赞数和下载数。
 */
const useDataEffect = (
  data: storeComponent,
  setLikedByUser: (value: any) => void,
  setLikesCount: (value: any) => void,
  setDownloadsCount: (value: any) => void,
) => {
  useEffect(() => {
    if (data) {
      setLikedByUser(data?.liked_by_user ?? false);
      setLikesCount(data?.liked_by_count ?? 0);
      setDownloadsCount(data?.downloads_count ?? 0);
    }
  }, [data, data?.liked_by_count, data?.liked_by_user, data?.downloads_count]);
};

export default useDataEffect;
