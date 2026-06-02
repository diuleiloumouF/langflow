import BaseModal from "../../../modals/baseModal";
import type { fetchErrorComponentType } from "../../../types/components";
import Loading from "../../ui/loading";

/**
 * 超时错误组件
 * 当请求超时时显示的弹窗，提供加载动画和重试按钮。
 */
export default function TimeoutErrorComponent({
  message,
  description,
  openModal,
  setRetry,
}: fetchErrorComponentType) {
  return (
    <>
      <BaseModal
        size="small-h-full"
        open={openModal}
        type="modal"
        onSubmit={() => {
          setRetry();
        }}
      >
        <BaseModal.Content>
          <div role="status" className="m-auto flex flex-col items-center">
            <Loading className={`h-16 w-16`} />
            <br></br>
            <span className="text-lg text-primary">{message}</span>
            <span className="text-center text-lg text-primary">
              {description}
            </span>
          </div>
        </BaseModal.Content>

        <BaseModal.Footer />
      </BaseModal>
    </>
  );
}
