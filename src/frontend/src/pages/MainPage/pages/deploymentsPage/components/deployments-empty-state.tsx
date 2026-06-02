import ForwardedIconComponent from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";

interface DeploymentsEmptyStateProps {
  onAction: () => void;
}

/**
 * 部署空状态组件
 * 当没有部署时显示的引导界面，提示用户创建第一个部署
 */
export default function DeploymentsEmptyState({
  onAction,
}: DeploymentsEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <h3 className="text-lg font-semibold">No Deployments</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Create your first deployment to run your flows in production.
      </p>
      <Button
        variant="outline"
        className="mt-4"
        data-testid="create-deployment-empty-btn"
        onClick={onAction}
      >
        <ForwardedIconComponent name="Plus" className="h-4 w-4" />
        Create Deployment
      </Button>
    </div>
  );
}
