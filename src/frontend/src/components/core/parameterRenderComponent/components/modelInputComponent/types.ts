export interface ModelOption {
  id?: string;
  name: string;
  icon: string;
  provider: string;
  metadata?: Record<string, unknown>;
}

export type SelectedModel = ModelOption;

export const getModelOptionKey = (
  option: Pick<ModelOption, "id" | "name" | "provider">,
): string => option.id || `${option.provider}::${option.name}`;

export const getModelOptionLabel = (
  option: Pick<ModelOption, "name" | "metadata">,
): string => {
  const displayName = option.metadata?.display_name;
  return typeof displayName === "string" && displayName.trim()
    ? displayName
    : option.name;
};

export interface ModelInputComponentType {
  options?: ModelOption[];
  placeholder?: string;
  externalOptions?: Record<string, unknown>;
  /** When true and options are empty, shows "No models enabled" in a clickable dropdown instead of loading state */
  showEmptyState?: boolean;
}
