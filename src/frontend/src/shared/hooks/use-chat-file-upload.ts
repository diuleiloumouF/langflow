import type { AxiosError } from "axios";
import {
  type ChangeEvent,
  type Dispatch,
  type SetStateAction,
  useCallback,
} from "react";
import { useTranslation } from "react-i18next";
import ShortUniqueId from "short-unique-id";
import {
  FS_ERROR_TEXT,
  SN_ERROR_TEXT,
} from "@/constants/file-upload-constants";
import { usePostUploadFile } from "@/controllers/API/queries/files/use-post-upload-file";
import { ENABLE_FILES_ON_PLAYGROUND } from "@/customization/feature-flags";
import useFileSizeValidator from "@/shared/hooks/use-file-size-validator";
import useAlertStore from "@/stores/alertStore";
import type { FilePreviewType } from "@/types/components";
import { isAllowedChatAttachmentFile } from "@/utils/file-validation";

// useChatFileUpload Hook 的参数接口
interface UseChatFileUploadParams {
  // 当前流程 ID
  currentFlowId: string;
  // 设置文件列表状态的方法
  setFiles: Dispatch<SetStateAction<FilePreviewType[]>>;
  // 是否在 Playground 页面（控制上传功能是否启用）
  playgroundPage?: boolean;
}

/**
 * useChatFileUpload Hook
 * 聊天文件上传功能，支持文件选择、剪贴板粘贴、文件验证和上传
 */
export const useChatFileUpload = ({
  currentFlowId,
  setFiles,
  playgroundPage = false,
}: UseChatFileUploadParams) => {
  // 国际化翻译函数
  const { t } = useTranslation();
  // 文件上传 API 的 mutation 方法
  const { mutate } = usePostUploadFile();
  // 错误提示方法
  const setErrorData = useAlertStore((state) => state.setErrorData);
  // 文件大小验证方法
  const { validateFileSize } = useFileSizeValidator();

  // 判断上传功能是否启用（非 Playground 页面或开启了文件上传功能）
  const isUploadEnabled = !playgroundPage || ENABLE_FILES_ON_PLAYGROUND;

  const uploadFile = useCallback(
    (file: File) => {
      if (!isUploadEnabled) {
        return;
      }

      if (!isAllowedChatAttachmentFile(file)) {
        setErrorData({
          title: "Error uploading file",
          list: [FS_ERROR_TEXT, SN_ERROR_TEXT],
        });
        return;
      }

      const uid = new ShortUniqueId();
      const id = uid.randomUUID(10);
      const type = file.type.split("/")[0] || "file";

      setFiles((prevFiles) => [
        ...prevFiles,
        { file, loading: true, error: false, id, type },
      ]);

      mutate(
        { file, id: currentFlowId },
        {
          onSuccess: (data) => {
            setFiles((prev) => {
              const newFiles = [...prev];
              const updatedIndex = newFiles.findIndex((f) => f.id === id);

              if (updatedIndex === -1) {
                return prev;
              }

              newFiles[updatedIndex] = {
                ...newFiles[updatedIndex],
                loading: false,
                path: data.file_path,
              };
              return newFiles;
            });
          },
          onError: (error: AxiosError<{ detail?: string }>) => {
            setFiles((prev) => {
              const newFiles = [...prev];
              const updatedIndex = newFiles.findIndex((f) => f.id === id);

              if (updatedIndex === -1) {
                return prev;
              }

              newFiles[updatedIndex] = {
                ...newFiles[updatedIndex],
                loading: false,
                error: true,
              };
              return newFiles;
            });

            setErrorData({
              title: "Error uploading file",
              list: [t("misc.fsErrorText"), SN_ERROR_TEXT],
            });
          },
        },
      );
    },
    [currentFlowId, isUploadEnabled, mutate, setErrorData, setFiles],
  );

  const handleFiles = useCallback(
    (uploadedFiles: FileList | null) => {
      if (!isUploadEnabled) {
        return;
      }

      if (!uploadedFiles || uploadedFiles.length === 0) {
        return;
      }

      const file = uploadedFiles[0];

      try {
        validateFileSize(file);
      } catch (error) {
        if (error instanceof Error) {
          setErrorData({ title: error.message });
        }
        return;
      }

      uploadFile(file);
    },
    [isUploadEnabled, setErrorData, uploadFile, validateFileSize],
  );

  const handleFileChange = useCallback(
    (event: ChangeEvent<HTMLInputElement> | ClipboardEvent) => {
      if (!isUploadEnabled) {
        if ("target" in event && event.target instanceof HTMLInputElement) {
          event.target.value = "";
        }
        return;
      }

      if ("clipboardData" in event) {
        const items = event.clipboardData?.items;
        if (!items) {
          return;
        }

        for (let i = 0; i < items.length; i++) {
          const file = items[i].getAsFile();
          if (file) {
            try {
              validateFileSize(file);
            } catch (error) {
              if (error instanceof Error) {
                setErrorData({ title: error.message });
              }
              return;
            }
            uploadFile(file);
            return;
          }
        }

        return;
      }

      const fileInput = event.target as HTMLInputElement;
      handleFiles(fileInput.files);
      fileInput.value = "";
    },
    [handleFiles, isUploadEnabled, setErrorData, uploadFile, validateFileSize],
  );

  return { handleFiles, handleFileChange };
};
