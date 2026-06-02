import ForwardedIconComponent from "@/components/common/genericIconComponent";
import {
  useDeleteGlobalVariables,
  useGetGlobalVariables,
} from "@/controllers/API/queries/variables";
import DeleteConfirmationModal from "@/modals/deleteConfirmationModal";
import useAlertStore from "@/stores/alertStore";
import { cn } from "@/utils/utils";

// 通用删除确认弹窗的属性接口
interface GeneralDeleteConfirmationModalProps {
  // 要删除的选项名称
  option: string;
  // 删除确认后的回调函数
  onConfirmDelete: () => void;
}

/**
 * 通用删除确认弹窗组件
 * 用于删除全局变量时的二次确认，支持 API 调用和错误处理
 */
const GeneralDeleteConfirmationModal = ({
  option,
  onConfirmDelete,
}: GeneralDeleteConfirmationModalProps) => {
  // 获取设置错误数据的方法
  const setErrorData = useAlertStore((state) => state.setErrorData);
  // 删除全局变量的 mutation 方法
  const { mutate: mutateDeleteGlobalVariable } = useDeleteGlobalVariables();
  // 获取全局变量列表数据
  const { data: globalVariables } = useGetGlobalVariables();

  /**
   * 处理删除操作
   * 根据变量名称查找对应的 ID 并执行删除
   */
  async function handleDelete(key: string) {
    // 如果没有全局变量数据则直接返回
    if (!globalVariables) return;
    // 根据名称查找变量的 ID
    const id = globalVariables.find((variable) => variable.name === key)?.id;
    if (id !== undefined) {
      // 找到 ID 后执行删除操作
      mutateDeleteGlobalVariable(
        { id },
        {
          onSuccess: () => {
            // 删除成功后触发确认回调
            onConfirmDelete();
          },
          onError: () => {
            // 删除失败时显示错误提示
            setErrorData({
              title: "Error deleting variable",
              list: [cn("ID not found for variable: ", key)],
            });
          },
        },
      );
    } else {
      // 未找到变量 ID 时显示错误
      setErrorData({
        title: "Error deleting variable",
        list: [cn("ID not found for variable: ", key)],
      });
    }
  }

  return (
    <>
      <DeleteConfirmationModal
        onConfirm={(e) => {
          // 阻止事件冒泡和默认行为
          e.stopPropagation();
          e.preventDefault();
          // 执行删除操作
          handleDelete(option);
        }}
        description={'variable "' + option + '"'}
        asChild
      >
        <button
          onClick={(e) => {
            e.stopPropagation();
          }}
          className="pr-1"
        >
          <ForwardedIconComponent
            name="Trash2"
            className={cn(
              "h-4 w-4 text-primary opacity-0 hover:text-status-red group-hover:opacity-100",
            )}
            aria-hidden="true"
          />
        </button>
      </DeleteConfirmationModal>
    </>
  );
};

export default GeneralDeleteConfirmationModal;
