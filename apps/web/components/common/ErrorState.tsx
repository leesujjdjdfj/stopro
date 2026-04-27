import { AlertTriangle } from "lucide-react";
import { Card } from "@/components/common/Card";
import { Button } from "@/components/common/Button";

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Card className="border-danger/25">
      <div className="flex gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-danger" />
        <div className="min-w-0">
          <p className="font-bold text-text">데이터를 불러오지 못했습니다</p>
          <p className="mt-1 text-sm leading-6 text-subText">{message}</p>
          {onRetry && (
            <Button className="mt-4" variant="secondary" onClick={onRetry}>
              다시 시도
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
