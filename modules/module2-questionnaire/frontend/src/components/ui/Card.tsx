import { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
}

function Card({ elevated = false, className, children, style, ...props }: CardProps) {
  const cardStyle: React.CSSProperties = {
    backgroundColor: "var(--color-bg-elevated)",
    borderRadius: "var(--radius-lg)",
    padding: "32px",
    boxShadow: elevated ? "var(--shadow-card)" : "none",
    border: "none",
    ...style,
  };

  return (
    <div style={cardStyle} className={className} {...props}>
      {children}
    </div>
  );
}

export { Card };
export type { CardProps };
