import type {
  AdviceResponse,
  SalesScript,
  ScriptScenario,
  ActionType,
  Priority,
} from "./types";

// ── 映射表 ───────────────────────────────────────────────────────────────────

const SCENARIO_LABELS: Record<ScriptScenario, string> = {
  opening: "開場（Opening）",
  objection: "異議處理（Objection）",
  closing: "收尾成交（Closing）",
  follow_up: "後續跟進（Follow Up）",
};

const ACTION_LABELS: Record<ActionType, string> = {
  schedule_consultation: "安排 2:1 商談",
  offer_trial: "提供試用品",
  escalate_to_senior: "轉請上線協助",
  send_educational_content: "推送衛教內容",
  hold_for_warming: "持續溫存，暫不推進",
};

const PRIORITY_LABELS: Record<Priority, string> = {
  high: "高優先",
  medium: "中優先",
  low: "低優先",
};

const LEVEL_LABELS: Record<string, string> = {
  low: "低",
  medium: "中",
  high: "高",
};

const PRIORITY_ORDER: Record<Priority, number> = { high: 0, medium: 1, low: 2 };

// ── 格式化日期 ────────────────────────────────────────────────────────────────

function formatTimestamp(): string {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  const hh = String(now.getHours()).padStart(2, "0");
  const min = String(now.getMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd} ${hh}:${min}`;
}

// ── 單一話術 Markdown ─────────────────────────────────────────────────────────

export function buildScriptMarkdown(script: SalesScript): string {
  const label = SCENARIO_LABELS[script.scenario] ?? script.scenario;
  const lines: string[] = [
    `## ${label}`,
    "",
    script.script || "（無建議）",
  ];

  if (script.taboo) {
    lines.push("", `> 禁忌提醒：${script.taboo}`);
  }

  return lines.join("\n");
}

// ── 完整建議 Markdown ─────────────────────────────────────────────────────────

export function buildFullAdviceMarkdown(
  response: AdviceResponse,
  options?: {
    includeTimestamp?: boolean;
    coachName?: string;
  }
): string {
  const { includeTimestamp = true, coachName } = options ?? {};
  const { summary, recommended_products, sales_scripts, next_actions } = response;
  const levelLabel = LEVEL_LABELS[summary.overall_level] ?? summary.overall_level;

  const lines: string[] = [];

  // ── 標題 ──
  lines.push("# Synergy 健康諮詢建議", "");

  // ── Frontmatter 引言 ──
  const metaLines: string[] = [];
  if (includeTimestamp) {
    metaLines.push(`產生時間：${formatTimestamp()}`);
  }
  metaLines.push(`客戶風險等級：**${levelLabel}**`);
  if (coachName) {
    metaLines.push(`健康顧問：${coachName}`);
  }
  metaLines.forEach((m) => lines.push(`> ${m}`));
  lines.push("");

  // ── 健康研判摘要 ──
  lines.push("## 健康研判摘要", "");
  lines.push(summary.narrative || "（無建議）", "");

  if (summary.key_risks.length > 0) {
    lines.push("### 關鍵風險", "");
    summary.key_risks.forEach((r) => lines.push(`- ${r}`));
    lines.push("");
  }

  if (summary.disclaimers.length > 0) {
    lines.push("### 免責聲明", "");
    summary.disclaimers.forEach((d) => lines.push(`- ${d}`));
    lines.push("");
  }

  // ── 推薦產品 ──
  lines.push("## 推薦產品", "");

  if (recommended_products.length === 0) {
    lines.push("（無建議）", "");
  } else {
    recommended_products.forEach((p, i) => {
      const pct = Math.round(p.confidence * 100);
      lines.push(`### ${i + 1}. ${p.name} (SKU: ${p.sku}) [信心 ${pct}%]`, "");
      lines.push(`推薦理由：${p.reason}`, "");
      if (p.image_url) {
        lines.push(`![product](${p.image_url})`, "");
      }
    });
  }

  // ── 行銷話術 ──
  lines.push("## 行銷話術", "");

  if (sales_scripts.length === 0) {
    lines.push("（無建議）", "");
  } else {
    sales_scripts.forEach((s) => {
      const label = SCENARIO_LABELS[s.scenario] ?? s.scenario;
      lines.push(`### ${label}`, "");
      lines.push(s.script || "（無建議）", "");
      if (s.taboo) {
        lines.push(`> 禁忌提醒：${s.taboo}`, "");
      }
    });
  }

  // ── 下一步行動 ──
  lines.push("## 下一步行動", "");

  if (next_actions.length === 0) {
    lines.push("（無建議）", "");
  } else {
    const sorted = [...next_actions].sort(
      (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
    );
    sorted.forEach((a, i) => {
      const actionLabel = ACTION_LABELS[a.action] ?? a.action;
      const priorityLabel = PRIORITY_LABELS[a.priority] ?? a.priority;
      lines.push(`${i + 1}. **${actionLabel}**（${priorityLabel}）— ${a.why}`);
    });
    lines.push("");
  }

  // ── 頁尾 ──
  lines.push("---", "*由 Synergy Questionnaire AI 產生*");

  return lines.join("\n");
}
