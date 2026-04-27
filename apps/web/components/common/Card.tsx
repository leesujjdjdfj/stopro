import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
  title,
  action
}: {
  children: ReactNode;
  className?: string;
  title?: string;
  action?: ReactNode;
}) {
  return (
    <section className={`rounded-[8px] border border-border bg-card p-5 shadow-soft ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between gap-3">
          {title ? <h2 className="text-base font-bold text-text">{title}</h2> : <span />}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
