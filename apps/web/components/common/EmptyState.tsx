import type { ReactNode } from "react";
import { Inbox } from "lucide-react";
import { Card } from "@/components/common/Card";

export function EmptyState({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
  return (
    <Card>
      <div className="flex flex-col items-center py-6 text-center">
        <Inbox className="h-9 w-9 text-subText" />
        <p className="mt-3 font-bold text-text">{title}</p>
        <p className="mt-1 max-w-sm text-sm leading-6 text-subText">{description}</p>
        {children && <div className="mt-4 flex flex-wrap justify-center gap-2">{children}</div>}
      </div>
    </Card>
  );
}
