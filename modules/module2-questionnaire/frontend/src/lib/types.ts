export type FieldType =
  | "single_choice"
  | "multi_choice"
  | "text"
  | "textarea"
  | "number"
  | "date"
  | "scale";

export interface FieldOption {
  value: string;
  label: string;
}

export interface FieldCondition {
  field_id: string;
  op: string;
  value: string | number | boolean;
}

export interface Field {
  field_id: string;
  label: string;
  type: FieldType;
  required: boolean;
  options: FieldOption[] | null;
  default: unknown;
  help_text: string | null;
  condition: FieldCondition | null;
  pii: boolean;
  order: number;
  min?: number | null;
  max?: number | null;
  unit?: string | null;
}

export interface Section {
  id: string;
  title: string;
  order: number;
  fields: Field[];
}

export interface QuestionnaireSchema {
  _meta: {
    source_file: string;
    source_sha256: string;
    generated_at: string;
    parser_version: string;
  };
  version: string;
  title: string;
  sections: Section[];
}

export type AnswerValue = string | number | boolean | string[] | null;
export type Answers = Record<string, AnswerValue>;

// ── AdviceResponse types (WBS 5.4) ──────────────────────────────────────────

export type OverallLevel = "low" | "medium" | "high";
export type ScriptScenario = "opening" | "objection" | "closing" | "follow_up";
export type ActionType =
  | "schedule_consultation"
  | "offer_trial"
  | "escalate_to_senior"
  | "send_educational_content"
  | "hold_for_warming";
export type Priority = "high" | "medium" | "low";

export interface HealthAssessmentSummary {
  key_risks: string[];
  overall_level: OverallLevel;
  narrative: string;
  disclaimers: string[];
}

export interface RecommendedProduct {
  sku: string;
  name: string;
  reason: string;
  image_url: string | null;
  confidence: number;
}

export interface SalesScript {
  scenario: ScriptScenario;
  script: string;
  taboo: string | null;
}

export interface NextAction {
  action: ActionType;
  why: string;
  priority: Priority;
}

export interface AdviceResponse {
  summary: HealthAssessmentSummary;
  recommended_products: RecommendedProduct[];
  sales_scripts: SalesScript[];
  next_actions: NextAction[];
}

export interface AdviceRequest {
  answers: Record<string, unknown>;
  locale?: "zh-TW" | "en";
  coach_level?: "new" | "experienced";
}
