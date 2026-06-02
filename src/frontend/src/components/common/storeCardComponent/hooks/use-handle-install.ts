import useAddFlow from "@/hooks/flows/use-add-flow";
import { getComponent } from "../../../../controllers/API";
import type { storeComponent } from "../../../../types/store";
import cloneFlowWithParent from "../../../../utils/storeUtils";

/**
 * 安装组件 Hook
 * 处理商店组件/流程的本地安装逻辑。
 * 获取组件数据、克隆流程并添加到本地，处理成功/失败状态。
 */
const useInstallComponent = (
  data: storeComponent,
  name: string,
  downloadsCount: number,
  setDownloadsCount: (value: any) => void,
  setLoading: (value: boolean) => void,
  setSuccessData: (value: { title: string }) => void,
  setErrorData: (value: { title: string; list: string[] }) => void,
) => {
  const addFlow = useAddFlow();

  // 处理安装操作
  const handleInstall = () => {
    const temp = downloadsCount; // 保存当前下载数，用于失败时恢复
    setDownloadsCount((old) => Number(old) + 1); // 乐观更新下载数
    setLoading(true);

    getComponent(data.id)
      .then((res) => {
        const newFlow = cloneFlowWithParent(res, res.id, data.is_component);
        addFlow({ flow: newFlow })
          .then((id) => {
            setSuccessData({
              title: `${name} Installed Successfully.`,
            });
            setLoading(false);
          })
          .catch((error) => {
            setLoading(false);
            setErrorData({
              title: `Error installing the ${name}`,
              list: [error.response.data.detail],
            });
          });
      })
      .catch((err) => {
        setLoading(false);
        setErrorData({
          title: `Error installing the ${name}`,
          list: [err.response.data.detail],
        });
        setDownloadsCount(temp);
      });
  };

  return { handleInstall };
};

export default useInstallComponent;
