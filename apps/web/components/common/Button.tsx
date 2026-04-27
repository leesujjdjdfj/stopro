import type { ButtonHTMLAttributes, ReactNode } from "react";

const variants = {
  primary: "bg-primary text-white shadow-sm active:bg-primary/90",
  secondary: "bg-cardSoft text-text active:bg-border",
  danger: "bg-danger text-white active:bg-danger/90",
  ghost: "bg-transparent text-subText active:bg-cardSoft"
};

export function Button({
  children,
  className = "",
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: keyof typeof variants;
}) {
  return (
    <button
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-[8px] px-4 text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
