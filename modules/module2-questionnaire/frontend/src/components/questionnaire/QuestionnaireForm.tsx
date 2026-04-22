import { useState } from "react";
import type { QuestionnaireSchema, Answers, AnswerValue } from "@/lib/types";
import { evaluateCondition } from "@/lib/conditions";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { QuestionnaireProgress } from "./QuestionnaireProgress";
import { SectionView } from "./SectionView";

interface QuestionnaireFormProps {
  schema: QuestionnaireSchema;
  onSubmit: (answers: Answers) => void;
}

export function QuestionnaireForm({ schema, onSubmit }: QuestionnaireFormProps) {
  const sortedSections = [...schema.sections].sort((a, b) => a.order - b.order);

  const [answers, setAnswers] = useState<Answers>({});
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const totalSections = sortedSections.length;
  const isFirstSection = currentSectionIndex === 0;
  const isLastSection = currentSectionIndex === totalSections - 1;
  const currentSection = sortedSections[currentSectionIndex];

  function handleChange(fieldId: string, value: AnswerValue) {
    setAnswers((prev) => ({ ...prev, [fieldId]: value }));
    // Clear error on change
    if (errors[fieldId]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[fieldId];
        return next;
      });
    }
  }

  function validateSection(sectionIndex: number): Record<string, string> {
    const section = sortedSections[sectionIndex];
    const newErrors: Record<string, string> = {};

    for (const field of section.fields) {
      // Skip hidden fields
      const visible = evaluateCondition(field.condition, answers);
      if (!visible) continue;

      if (!field.required) continue;

      const val = answers[field.field_id];

      // Empty check
      const isEmpty =
        val === null ||
        val === undefined ||
        val === "" ||
        (Array.isArray(val) && val.length === 0);

      if (isEmpty) {
        newErrors[field.field_id] = "此欄位為必填";
        continue;
      }

      // Number range check
      if (field.type === "number" && typeof val === "number") {
        if (field.min != null && val < field.min) {
          newErrors[field.field_id] = `最小值為 ${field.min}`;
        } else if (field.max != null && val > field.max) {
          newErrors[field.field_id] = `最大值為 ${field.max}`;
        }
      }
    }

    return newErrors;
  }

  function handleNext() {
    const sectionErrors = validateSection(currentSectionIndex);
    if (Object.keys(sectionErrors).length > 0) {
      setErrors((prev) => ({ ...prev, ...sectionErrors }));
      return;
    }
    setCurrentSectionIndex((i) => i + 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handlePrev() {
    setCurrentSectionIndex((i) => i - 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleSubmit() {
    // Full validation across all sections
    const allErrors: Record<string, string> = {};
    for (let i = 0; i < totalSections; i++) {
      const sectionErrors = validateSection(i);
      Object.assign(allErrors, sectionErrors);
    }

    if (Object.keys(allErrors).length > 0) {
      setErrors(allErrors);
      // Also validate current section to show errors
      const currentErrors = validateSection(currentSectionIndex);
      if (Object.keys(currentErrors).length > 0) {
        return;
      }
    }

    onSubmit(answers);
  }

  const sectionTitles = sortedSections.map((s) => s.title);

  return (
    <div
      style={{
        width: "100%",
        maxWidth: "720px",
        marginLeft: "auto",
        marginRight: "auto",
        paddingLeft: "24px",
        paddingRight: "24px",
        paddingTop: "40px",
        paddingBottom: "60px",
      }}
    >
      {/* Form title */}
      <div style={{ textAlign: "center", marginBottom: "40px" }}>
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(28px, 4vw, 40px)",
            fontWeight: 600,
            lineHeight: 1.07,
            letterSpacing: "-0.28px",
            color: "var(--color-fg)",
            margin: "0 0 12px",
          }}
        >
          {schema.title}
        </h1>
        <p
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "17px",
            fontWeight: 400,
            lineHeight: 1.47,
            letterSpacing: "-0.374px",
            color: "var(--color-fg-muted)",
            margin: 0,
          }}
        >
          請依序完成以下各段問卷
        </p>
      </div>

      {/* Progress */}
      <QuestionnaireProgress
        currentIndex={currentSectionIndex}
        total={totalSections}
        sectionTitles={sectionTitles}
      />

      {/* Section card */}
      <Card elevated style={{ marginBottom: "32px" }}>
        <SectionView
          section={currentSection}
          answers={answers}
          errors={errors}
          onChange={handleChange}
        />
      </Card>

      {/* Navigation buttons */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "16px",
        }}
      >
        <Button
          variant="secondary"
          size="md"
          onClick={handlePrev}
          disabled={isFirstSection}
          style={{ visibility: isFirstSection ? "hidden" : "visible" }}
        >
          上一步
        </Button>

        <span
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "13px",
            fontWeight: 400,
            color: "var(--color-fg-subtle)",
          }}
        >
          {currentSectionIndex + 1} / {totalSections}
        </span>

        {isLastSection ? (
          <Button variant="primary" size="md" onClick={handleSubmit}>
            提交問卷
          </Button>
        ) : (
          <Button variant="primary" size="md" onClick={handleNext}>
            下一步
          </Button>
        )}
      </div>
    </div>
  );
}
