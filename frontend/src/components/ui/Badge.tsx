import { CSSProperties } from "react";

type Variant = "default" | "success" | "warning" | "danger" | "info" | "accent";

const variantClass: Record<Variant, string> = {
  default: "badge-default",
  success: "badge-success",
  warning: "badge-warning",
  danger: "badge-danger",
  info: "badge-info",
  accent: "badge-accent",
};

interface BadgeProps {
  variant?: Variant;
  children: React.ReactNode;
  className?: string;
  style?: CSSProperties;
}

export default function Badge({ variant = "default", children, className = "", style }: BadgeProps) {
  return <span className={`badge ${variantClass[variant]} ${className}`} style={style}>{children}</span>;
}
