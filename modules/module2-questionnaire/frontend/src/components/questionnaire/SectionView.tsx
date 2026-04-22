import type { Section, Answers, AnswerValue } from "@/lib/types";
import { evaluateCondition } from "@/lib/conditions";
import { FieldInput } from "./FieldInput";

interface SectionViewProps {
  section: Section;
  answers: Answers;
  errors: Record<string, string>;
  onChange: (fieldId: string, value: AnswerValue) => void;
}

export function SectionView({ section, answers, errors, onChange }: SectionViewProps) {
  const sortedFields = [...section.fields].sort((a, b) => a.order - b.order);

  return (
    <div>
      {/* Section title */}
      <h2
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "22px",
          fontWeight: 700,
          lineHeight: 1.18,
          letterSpacing: "-0.26px",
          color: "var(--color-fg)",
          margin: "0 0 24px",
        }}
      >
        {section.title}
      </h2>

      {/* Fields */}
      <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
        {sortedFields.map((field) => {
          // Conditional display: hide field if condition is not met
          const visible = evaluateCondition(field.condition, answers);
          if (!visible) return null;

          return (
            <FieldInput
              key={field.field_id}
              field={field}
              value={answers[field.field_id] ?? null}
              error={errors[field.field_id]}
              onChange={(val) => onChange(field.field_id, val)}
            />
          );
        })}
      </div>
    </div>
  );
}
