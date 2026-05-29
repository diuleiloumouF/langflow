import { useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import { CustomOpenAIModel } from "./use-get-custom-openai-models";

export interface SaveCustomOpenAIModelPayload {
  id?: string;
  model_name: string;
  display_name: string;
  base_url: string;
  api_key?: string;
  model_type: "llm" | "embeddings";
  enabled_by_default: boolean;
}

export const usePostCustomOpenAIModel: useMutationFunctionType<
  undefined,
  SaveCustomOpenAIModelPayload,
  CustomOpenAIModel,
  Error
> = (options) => {
  const { mutate } = UseRequestProcessor();

  const postCustomOpenAIModelFn = async (
    payload: SaveCustomOpenAIModelPayload,
  ): Promise<CustomOpenAIModel> => {
    const response = await api.post<CustomOpenAIModel>(
      `${getURL("MODELS")}/custom-openai-models`,
      payload,
    );
    return response.data;
  };

  return mutate(["usePostCustomOpenAIModel"], postCustomOpenAIModelFn, options);
};
