import type { Answers, FieldCondition } from "./types";

export function evaluateCondition(
  cond: FieldCondition | null,
  answers: Answers,
): boolean {
  if (!cond) return true;
  const v = answers[cond.field_id];
  if (v === null || v === undefined) return false;
  switch (cond.op) {
    case "==":
      return v === cond.value;
    case "!=":
      return v !== cond.value;
    case ">=":
      return (
        typeof v === "number" &&
        typeof cond.value === "number" &&
        v >= cond.value
      );
    case "<=":
      return (
        typeof v === "number" &&
        typeof cond.value === "number" &&
        v <= cond.value
      );
    case "contains":
      return (
        typeof v === "string" &&
        typeof cond.value === "string" &&
        v.includes(cond.value)
      );
    case "in":
      return Array.isArray(cond.value) && cond.value.includes(v as string);
    default:
      return true; // 未知 op 保守顯示
  }
}
