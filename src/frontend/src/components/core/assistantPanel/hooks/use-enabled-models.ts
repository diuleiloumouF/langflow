import { useMemo } from "react";
import { useGetEnabledModels } from "@/controllers/API/queries/models/use-get-enabled-models";
import { useGetModelProviders } from "@/controllers/API/queries/models/use-get-model-providers";

interface FilteredProvider {
  provider: string;
  icon: string;
  models: Array<{
    id?: string;
    model_name: string;
    metadata?: Record<string, unknown>;
  }>;
}

interface UseEnabledModelsReturn {
  hasEnabledModels: boolean;
  filteredProviders: FilteredProvider[];
  isLoading: boolean;
}

export function useEnabledModels(): UseEnabledModelsReturn {
  const { data: providersData = [], isLoading } = useGetModelProviders({});
  const { data: enabledModelsData } = useGetEnabledModels();

  const filteredProviders = useMemo(() => {
    const enabledModels = enabledModelsData?.enabled_models || {};

    return providersData
      .filter((provider) => provider.is_enabled)
      .map((provider) => {
        const providerEnabledModels = enabledModels[provider.provider] || {};
        return {
          provider: provider.provider,
          icon: provider.icon || "Bot",
          models: provider.models.filter(
            (model) =>
              providerEnabledModels[model.id || model.model_name] === true &&
              model.metadata?.model_type !== "embeddings",
          ),
        };
      })
      .filter((provider) => provider.models.length > 0);
  }, [providersData, enabledModelsData]);

  const hasEnabledModels = filteredProviders.length > 0;

  return { hasEnabledModels, filteredProviders, isLoading };
}
