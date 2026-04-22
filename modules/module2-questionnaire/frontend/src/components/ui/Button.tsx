import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const baseStyles: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  fontFamily: "var(--font-sans)",
  fontWeight: 400,
  lineHeight: 1,
  letterSpacing: "-0.374px",
  border: "1px solid transparent",
  cursor: "pointer",
  transition: `background-color var(--duration-fast) ease, opacity var(--duration-fast) ease`,
  borderRadius: "var(--radius-sm)",
  textDecoration: "none",
  whiteSpace: "nowrap",
};

const sizeMap: Record<Size, React.CSSProperties> = {
  sm: { fontSize: "14px", padding: "6px 12px" },
  md: { fontSize: "17px", padding: "8px 15px" },
  lg: { fontSize: "18px", padding: "10px 20px", fontWeight: 300 },
};

const variantStyles: Record<Variant, React.CSSProperties> = {
  primary: {
    backgroundColor: "var(--color-accent)",
    color: "#ffffff",
    borderColor: "transparent",
  },
  secondary: {
    backgroundColor: "transparent",
    color: "var(--color-link)",
    borderColor: "var(--color-link)",
  },
  ghost: {
    backgroundColor: "transparent",
    color: "var(--color-link)",
    borderColor: "transparent",
    borderRadius: "var(--radius-pill)",
  },
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading = false, disabled, children, style, ...props }, ref) => {
    const isDisabled = disabled || loading;
    const computedStyle: React.CSSProperties = {
      ...baseStyles,
      ...sizeMap[size],
      ...variantStyles[variant],
      opacity: isDisabled ? 0.5 : 1,
      cursor: isDisabled ? "not-allowed" : "pointer",
      ...style,
    };

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        style={computedStyle}
        onMouseEnter={(e) => {
          if (!isDisabled && variant === "primary") {
            (e.currentTarget as HTMLButtonElement).style.backgroundColor = "var(--color-accent-hover)";
          }
        }}
        onMouseLeave={(e) => {
          if (!isDisabled && variant === "primary") {
            (e.currentTarget as HTMLButtonElement).style.backgroundColor = "var(--color-accent)";
          }
        }}
        onFocus={(e) => {
          (e.currentTarget as HTMLButtonElement).style.outline = "2px solid var(--color-focus)";
          (e.currentTarget as HTMLButtonElement).style.outlineOffset = "2px";
        }}
        onBlur={(e) => {
          (e.currentTarget as HTMLButtonElement).style.outline = "none";
        }}
        {...props}
      >
        {loading ? (
          <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
            <span
              style={{
                width: "14px",
                height: "14px",
                border: "2px solid currentColor",
                borderTopColor: "transparent",
                borderRadius: "50%",
                display: "inline-block",
                animation: "spin 0.7s linear infinite",
              }}
            />
            {children}
          </span>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button };
export type { ButtonProps, Variant, Size };
