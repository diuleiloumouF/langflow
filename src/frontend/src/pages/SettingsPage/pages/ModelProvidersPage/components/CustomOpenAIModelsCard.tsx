import { useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import ForwardedIconComponent from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
  useDeleteCustomOpenAIModel,
  useGetCustomOpenAIModels,
  usePostCustomOpenAIModel,
} from "@/controllers/API/queries/models";
import useAlertStore from "@/stores/alertStore";

/** 模型类型枚举 */
type ModelType = "llm" | "embeddings";

/** 自定义 OpenAI 模型表单状态 */
interface FormState {
  id?: string;
  display_name: string;
  model_name: string;
  base_url: string;
  api_key: string;
  model_type: ModelType;
  enabled_by_default: boolean;
}

const EMPTY_FORM: FormState = {
  display_name: "",
  model_name: "",
  base_url: "",
  api_key: "",
  model_type: "llm",
  enabled_by_default: true,
};

const CustomOpenAIModelsCard = () => {
  const queryClient = useQueryClient();
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [isEditing, setIsEditing] = useState(false);

  const { data: customModels = [], isLoading } = useGetCustomOpenAIModels();
  const { mutateAsync: saveCustomModel, isPending: isSaving } =
    usePostCustomOpenAIModel();
  const { mutateAsync: deleteCustomModel, isPending: isDeleting } =
    useDeleteCustomOpenAIModel();

  const canSave = useMemo(() => {
    return (
      form.display_name.trim() &&
      form.model_name.trim() &&
      form.base_url.trim() &&
      (isEditing ? true : form.api_key.trim())
    );
  }, [form, isEditing]);

  const refreshModelQueries = () => {
    queryClient.invalidateQueries({ queryKey: ["useGetCustomOpenAIModels"] });
    queryClient.invalidateQueries({ queryKey: ["useGetModelProviders"] });
    queryClient.invalidateQueries({ queryKey: ["useGetEnabledModels"] });
  };

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setIsEditing(false);
  };

  const handleSave = async () => {
    try {
      await saveCustomModel(form);
      refreshModelQueries();
      setSuccessData({
        title: isEditing ? "Custom model updated" : "Custom model added",
      });
      resetForm();
    } catch (error) {
      const message =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed to save custom model";
      setErrorData({ title: "Save failed", list: [message] });
    }
  };

  const handleEdit = (model: (typeof customModels)[number]) => {
    setForm({
      id: model.id,
      display_name: model.display_name,
      model_name: model.model_name,
      base_url: model.base_url,
      api_key: "",
      model_type: model.model_type,
      enabled_by_default: model.enabled_by_default,
    });
    setIsEditing(true);
  };

  const handleDelete = async (modelId: string) => {
    try {
      await deleteCustomModel({ modelId });
      refreshModelQueries();
      setSuccessData({ title: "Custom model deleted" });
      if (form.id === modelId) {
        resetForm();
      }
    } catch (error) {
      const message =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed to delete custom model";
      setErrorData({ title: "Delete failed", list: [message] });
    }
  };

  return (
    <div className="rounded-lg border bg-background p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold">
            Custom OpenAI-compatible Models
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Add models served by any OpenAI-compatible endpoint using a custom
            base URL, API key, and model name.
          </p>
        </div>
        <ForwardedIconComponent
          name="OpenAI"
          className="h-5 w-5 text-primary"
        />
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <Input
          placeholder="Display name"
          value={form.display_name}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              display_name: event.target.value,
            }))
          }
        />
        <Input
          placeholder="Model name"
          value={form.model_name}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              model_name: event.target.value,
            }))
          }
        />
        <Input
          placeholder="Base URL"
          value={form.base_url}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              base_url: event.target.value,
            }))
          }
        />
        <Input
          placeholder={isEditing ? "Replace API key" : "API key"}
          type="password"
          value={form.api_key}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              api_key: event.target.value,
            }))
          }
        />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-4 text-sm">
        <label className="flex items-center gap-2">
          <input
            type="radio"
            checked={form.model_type === "llm"}
            onChange={() =>
              setForm((current) => ({ ...current, model_type: "llm" }))
            }
          />
          Language model
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            checked={form.model_type === "embeddings"}
            onChange={() =>
              setForm((current) => ({ ...current, model_type: "embeddings" }))
            }
          />
          Embedding model
        </label>
        <label className="flex items-center gap-2">
          <Checkbox
            checked={form.enabled_by_default}
            onCheckedChange={(checked) =>
              setForm((current) => ({
                ...current,
                enabled_by_default: checked === true,
              }))
            }
          />
          Enabled by default
        </label>
      </div>

      <div className="mt-4 flex gap-2">
        <Button
          onClick={handleSave}
          disabled={!canSave || isSaving}
          loading={isSaving}
        >
          {isEditing ? "Update model" : "Add model"}
        </Button>
        {isEditing && (
          <Button variant="outline" onClick={resetForm}>
            Cancel
          </Button>
        )}
      </div>

      <div className="mt-6 flex flex-col gap-2">
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Loading models...</div>
        ) : customModels.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No custom OpenAI-compatible models configured yet.
          </div>
        ) : (
          customModels.map((model) => (
            <div
              key={model.id}
              className="flex items-center justify-between rounded-md border px-3 py-3"
            >
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">
                  {model.display_name}
                </div>
                <div className="truncate text-xs text-muted-foreground">
                  {model.model_name} · {model.base_url}
                </div>
                <div className="truncate text-xs text-muted-foreground">
                  {model.model_type === "llm"
                    ? "Language model"
                    : "Embedding model"}
                  {" · "}
                  {model.api_key || "API key configured"}
                </div>
              </div>
              <div className="ml-4 flex shrink-0 gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEdit(model)}
                >
                  Edit
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleDelete(model.id)}
                  disabled={isDeleting}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default CustomOpenAIModelsCard;
