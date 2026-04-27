import { ShieldCheck } from "lucide-react";
import { DISCLAIMER } from "@/lib/constants";

export function DisclaimerBanner() {
  return (
    <div className="flex items-start gap-2 rounded-[8px] border border-warning/25 bg-warning/10 px-4 py-3 text-xs leading-5 text-amber-700">
      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
      <p>{DISCLAIMER}</p>
    </div>
  );
}
