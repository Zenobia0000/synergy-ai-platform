import { InputHTMLAttributes, useId } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

function Input({ label, error, style, ...props }: InputProps) {
  const id = useId();

  const inputStyle: React.CSSProperties = {
    display: "block",
    width: "100%",
    padding: "8px 14px",
    fontSize: "17px",
    fontFamily: "var(--font-sans)",
    fontWeight: 400,
    lineHeight: 1.47,
    letterSpacing: "-0.374px",
    color: "var(--color-fg)",
    backgroundColor: "var(--color-btn-filter, #fafafc)",
    border: `1px solid ${error ? "var(--color-error)" : "var(--color-border)"}`,
    borderRadius: "var(--radius-md)",
    outline: "none",
    transition: `border-color var(--duration-fast) ease, box-shadow var(--duration-fast) ease`,
    boxSizing: "border-box",
    ...style,
  };

  const labelStyle: React.CSSProperties = {
    display: "block",
    fontSize: "14px",
    fontFamily: "var(--font-sans)",
    fontWeight: 600,
    lineHeight: 1.29,
    letterSpacing: "-0.224px",
    color: "var(--color-fg)",
    marginBottom: "6px",
  };

  const errorStyle: React.CSSProperties = {
    fontSize: "12px",
    fontFamily: "var(--font-sans)",
    fontWeight: 400,
    lineHeight: 1.33,
    letterSpacing: "-0.12px",
    color: "var(--color-error)",
    marginTop: "4px",
  };

  return (
    <div>
      <label htmlFor={id} style={labelStyle}>
        {label}
      </label>
      <input
        id={id}
        style={inputStyle}
        onFocus={(e) => {
          (e.currentTarget as HTMLInputElement).style.borderColor = "var(--color-accent)";
          (e.currentTarget as HTMLInputElement).style.boxShadow = "0 0 0 3px rgba(0, 113, 227, 0.18)";
        }}
        onBlur={(e) => {
          (e.currentTarget as HTMLInputElement).style.borderColor = error
            ? "var(--color-error)"
            : "var(--color-border)";
          (e.currentTarget as HTMLInputElement).style.boxShadow = "none";
        }}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      />
      {error && (
        <p id={`${id}-error`} style={errorStyle} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

export { Input };
export type { InputProps };
