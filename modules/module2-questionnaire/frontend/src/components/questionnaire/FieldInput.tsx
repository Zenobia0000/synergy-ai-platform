import { useId } from "react";
import type { Field, AnswerValue } from "@/lib/types";

interface FieldInputProps {
  field: Field;
  value: AnswerValue;
  error?: string;
  onChange: (value: AnswerValue) => void;
}

const labelStyle: React.CSSProperties = {
  display: "block",
  fontFamily: "var(--font-sans)",
  fontSize: "15px",
  fontWeight: 600,
  lineHeight: 1.33,
  letterSpacing: "-0.24px",
  color: "var(--color-fg)",
  marginBottom: "6px",
};

const helpStyle: React.CSSProperties = {
  fontFamily: "var(--font-sans)",
  fontSize: "12px",
  fontWeight: 400,
  lineHeight: 1.33,
  letterSpacing: "-0.12px",
  color: "var(--color-fg-subtle)",
  marginTop: "4px",
};

const errorStyle: React.CSSProperties = {
  fontFamily: "var(--font-sans)",
  fontSize: "12px",
  fontWeight: 400,
  lineHeight: 1.33,
  letterSpacing: "-0.12px",
  color: "var(--color-error)",
  marginTop: "4px",
};

const baseInputStyle: React.CSSProperties = {
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
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius-md)",
  outline: "none",
  transition: "border-color var(--duration-fast) ease, box-shadow var(--duration-fast) ease",
  boxSizing: "border-box",
};

function handleFocus(e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) {
  e.currentTarget.style.borderColor = "var(--color-accent)";
  e.currentTarget.style.boxShadow = "0 0 0 3px rgba(0, 113, 227, 0.18)";
}

function handleBlur(
  e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>,
  hasError: boolean,
) {
  e.currentTarget.style.borderColor = hasError ? "var(--color-error)" : "var(--color-border)";
  e.currentTarget.style.boxShadow = "none";
}

export function FieldInput({ field, value, error, onChange }: FieldInputProps) {
  const uid = useId();
  const isRequired = field.required;

  const labelNode = (
    <span style={labelStyle}>
      {field.label}
      {isRequired && (
        <span
          aria-hidden="true"
          style={{ color: "var(--color-error)", marginLeft: "3px" }}
        >
          *
        </span>
      )}
    </span>
  );

  const helpNode = field.help_text ? (
    <p style={helpStyle}>{field.help_text}</p>
  ) : null;

  const errorNode = error ? (
    <p id={`${uid}-error`} style={errorStyle} role="alert">
      {error}
    </p>
  ) : null;

  const borderColor = error ? "var(--color-error)" : "var(--color-border)";

  // --- single_choice ---
  if (field.type === "single_choice" && field.options) {
    return (
      <fieldset style={{ border: "none", padding: 0, margin: 0 }}>
        <legend style={labelStyle}>
          {field.label}
          {isRequired && (
            <span aria-hidden="true" style={{ color: "var(--color-error)", marginLeft: "3px" }}>
              *
            </span>
          )}
        </legend>
        {helpNode}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "8px" }}>
          {field.options.map((opt) => (
            <label
              key={opt.value}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                cursor: "pointer",
                fontFamily: "var(--font-sans)",
                fontSize: "15px",
                fontWeight: 400,
                lineHeight: 1.33,
                color: "var(--color-fg)",
              }}
            >
              <input
                type="radio"
                name={`field-${field.field_id}`}
                value={opt.value}
                checked={value === opt.value}
                onChange={() => onChange(opt.value)}
                style={{ accentColor: "var(--color-accent)", width: "16px", height: "16px" }}
              />
              {opt.label}
            </label>
          ))}
        </div>
        {errorNode}
      </fieldset>
    );
  }

  // --- multi_choice ---
  if (field.type === "multi_choice" && field.options) {
    const selected: string[] = Array.isArray(value) ? (value as string[]) : [];
    function toggle(v: string) {
      if (selected.includes(v)) {
        onChange(selected.filter((x) => x !== v));
      } else {
        onChange([...selected, v]);
      }
    }
    return (
      <fieldset style={{ border: "none", padding: 0, margin: 0 }}>
        <legend style={labelStyle}>
          {field.label}
          {isRequired && (
            <span aria-hidden="true" style={{ color: "var(--color-error)", marginLeft: "3px" }}>
              *
            </span>
          )}
        </legend>
        {helpNode}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "8px" }}>
          {field.options.map((opt) => (
            <label
              key={opt.value}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                cursor: "pointer",
                fontFamily: "var(--font-sans)",
                fontSize: "15px",
                fontWeight: 400,
                lineHeight: 1.33,
                color: "var(--color-fg)",
              }}
            >
              <input
                type="checkbox"
                value={opt.value}
                checked={selected.includes(opt.value)}
                onChange={() => toggle(opt.value)}
                style={{ accentColor: "var(--color-accent)", width: "16px", height: "16px" }}
              />
              {opt.label}
            </label>
          ))}
        </div>
        {errorNode}
      </fieldset>
    );
  }

  // --- textarea ---
  if (field.type === "textarea") {
    return (
      <div>
        <label htmlFor={uid} style={labelStyle}>
          {field.label}
          {isRequired && (
            <span aria-hidden="true" style={{ color: "var(--color-error)", marginLeft: "3px" }}>
              *
            </span>
          )}
        </label>
        {helpNode}
        <textarea
          id={uid}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
          aria-invalid={!!error}
          aria-describedby={error ? `${uid}-error` : undefined}
          rows={4}
          style={{
            ...baseInputStyle,
            resize: "vertical",
            borderColor,
          }}
          onFocus={handleFocus}
          onBlur={(e) => handleBlur(e, !!error)}
        />
        {errorNode}
      </div>
    );
  }

  // --- number ---
  if (field.type === "number") {
    return (
      <div>
        <label htmlFor={uid} style={labelStyle}>
          {field.label}
          {isRequired && (
            <span aria-hidden="true" style={{ color: "var(--color-error)", marginLeft: "3px" }}>
              *
            </span>
          )}
        </label>
        {helpNode}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <input
            id={uid}
            type="number"
            value={typeof value === "number" ? value : ""}
            min={field.min ?? undefined}
            max={field.max ?? undefined}
            onChange={(e) => {
              const n = e.target.value === "" ? null : Number(e.target.value);
              onChange(n);
            }}
            aria-invalid={!!error}
            aria-describedby={error ? `${uid}-error` : undefined}
            style={{ ...baseInputStyle, borderColor, maxWidth: "180px" }}
            onFocus={handleFocus}
            onBlur={(e) => handleBlur(e, !!error)}
          />
          {field.unit && (
            <span
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "15px",
                fontWeight: 400,
                color: "var(--color-fg-muted)",
              }}
            >
              {field.unit}
            </span>
          )}
        </div>
        {errorNode}
      </div>
    );
  }

  // --- date ---
  if (field.type === "date") {
    return (
      <div>
        <label htmlFor={uid} style={labelStyle}>
          {field.label}
          {isRequired && (
            <span aria-hidden="true" style={{ color: "var(--color-error)", marginLeft: "3px" }}>
              *
            </span>
          )}
        </label>
        {helpNode}
        <input
          id={uid}
          type="date"
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
          aria-invalid={!!error}
          aria-describedby={error ? `${uid}-error` : undefined}
          style={{ ...baseInputStyle, borderColor, maxWidth: "220px" }}
          onFocus={handleFocus}
          onBlur={(e) => handleBlur(e, !!error)}
        />
        {errorNode}
      </div>
    );
  }

  // --- scale ---
  if (field.type === "scale") {
    const scaleMin = field.min ?? 1;
    const scaleMax = field.max ?? 10;
    const steps = Array.from({ length: scaleMax - scaleMin + 1 }, (_, i) => scaleMin + i);
    return (
      <fieldset style={{ border: "none", padding: 0, margin: 0 }}>
        <legend style={labelStyle}>
          {field.label}
          {isRequired && (
            <span aria-hidden="true" style={{ color: "var(--color-error)", marginLeft: "3px" }}>
              *
            </span>
          )}
        </legend>
        {helpNode}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "8px" }}>
          {steps.map((n) => {
            const active = value === n;
            return (
              <button
                key={n}
                type="button"
                onClick={() => onChange(n)}
                style={{
                  width: "40px",
                  height: "40px",
                  borderRadius: "var(--radius-sm)",
                  border: `1px solid ${active ? "var(--color-accent)" : "var(--color-border)"}`,
                  backgroundColor: active ? "var(--color-accent)" : "var(--color-btn-filter)",
                  color: active ? "#ffffff" : "var(--color-fg)",
                  fontFamily: "var(--font-sans)",
                  fontSize: "15px",
                  fontWeight: active ? 600 : 400,
                  cursor: "pointer",
                  transition: "background-color var(--duration-fast) ease",
                }}
                aria-pressed={active}
              >
                {n}
              </button>
            );
          })}
        </div>
        {errorNode}
      </fieldset>
    );
  }

  // --- text (default) ---
  return (
    <div>
      {labelNode}
      {helpNode}
      <input
        id={uid}
        type="text"
        value={typeof value === "string" ? value : ""}
        onChange={(e) => onChange(e.target.value)}
        aria-invalid={!!error}
        aria-describedby={error ? `${uid}-error` : undefined}
        style={{ ...baseInputStyle, borderColor }}
        onFocus={handleFocus}
        onBlur={(e) => handleBlur(e, !!error)}
      />
      {errorNode}
    </div>
  );
}
