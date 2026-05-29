import { useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface DeleteCustomOpenAIModelPayload {
  modelId: string;
}

export const useDeleteCustomOpenAIModel: useMutationFunctionType<
  undefined,
  DeleteCustomOpenAIModelPayload,
  void,
  Error
> = (options) => {
  const { mutate } = UseRequestProcessor();

  const deleteCustomOpenAIModelFn = async ({
    modelId,
  }: DeleteCustomOpenAIModelPayload): Promise<void> => {
    await api.delete(`${getURL("MODELS")}/custom-openai-models/${modelId}`);
  };

  return mutate(
    ["useDeleteCustomOpenAIModel"],
    deleteCustomOpenAIModelFn,
    options,
  );
};
