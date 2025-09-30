import { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "danger";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants: Record<typeof variant, string> = {
    default: "bg-surface-muted text-foreground",
    success: "bg-positive/10 text-positive",
    danger: "bg-negative/10 text-negative",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
