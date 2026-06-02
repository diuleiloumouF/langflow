import ForwardedIconComponent from "@/components/common/genericIconComponent";
import GlobalVariableModal from "@/components/core/GlobalVariableModal/GlobalVariableModal";
import { CommandItem } from "@/components/ui/command";
import { cn } from "@/utils/utils";

/**
 * 通用全局变量弹窗组件
 * 提供一个命令面板中的选项，用于打开添加新变量的弹窗
 */
const GeneralGlobalVariableModal = () => {
  return (
    <>
      <GlobalVariableModal disabled={false}>
        <CommandItem value="doNotFilter-addNewVariable">
          <ForwardedIconComponent
            name="Plus"
            className={cn("mr-2 h-4 w-4 text-primary")}
            aria-hidden="true"
          />
          <span>Add New Variable</span>
        </CommandItem>
      </GlobalVariableModal>
    </>
  );
};

export default GeneralGlobalVariableModal;
