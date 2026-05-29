import { useQueryFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface CustomOpenAIModel {
  id: string;
  model_name: string;
  display_name: string;
  base_url: string;
  api_key: string | null;
  has_api_key: boolean;
  model_type: "llm" | "embeddings";
  enabled_by_default: boolean;
}

export const useGetCustomOpenAIModels: useQueryFunctionType<
  undefined,
  CustomOpenAIModel[]
> = (_, options) => {
  const { query } = UseRequestProcessor();

  const getCustomOpenAIModelsFn = async (): Promise<CustomOpenAIModel[]> => {
    const response = await api.get<CustomOpenAIModel[]>(
      `${getURL("MODELS")}/custom-openai-models`,
    );
    return response.data;
  };

  return query(["useGetCustomOpenAIModels"], getCustomOpenAIModelsFn, {
    refetchOnWindowFocus: false,
    ...options,
  });
};
