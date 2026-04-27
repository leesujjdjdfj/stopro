import type { ReactNode } from "react";

const tones = {
  blue: "bg-primary/10 text-primary",
  green: "bg-safe/10 text-safe",
  orange: "bg-warning/10 text-warning",
  red: "bg-danger/10 text-danger",
  gray: "bg-cardSoft text-subText",
  dark: "bg-text text-white"
};

export function Badge({ children, tone = "gray" }: { children: ReactNode; tone?: keyof typeof tones }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${tones[tone]}`}>
      {children}
    </span>
  );
}
