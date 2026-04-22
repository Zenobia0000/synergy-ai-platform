import type { NextAction, ActionType, Priority } from "@/lib/types";

interface NextActionsListProps {
  actions: NextAction[];
}

const ACTION_LABELS: Record<ActionType, string> = {
  schedule_consultation: "安排 2:1 商談",
  offer_trial: "提供試用品",
  escalate_to_senior: "轉請上線協助",
  send_educational_content: "推送衛教內容",
  hold_for_warming: "持續溫存，暫不推進",
};

const PRIORITY_CONFIG: Record<
  Priority,
  { label: string; color: string; bg: string; border: string }
> = {
  high: {
    label: "高",
    color: "var(--color-error)",
    bg: "rgba(255, 59, 48, 0.08)",
    border: "rgba(255, 59, 48, 0.2)",
  },
  medium: {
    label: "中",
    color: "var(--color-warning)",
    bg: "rgba(255, 159, 10, 0.08)",
    border: "rgba(255, 159, 10, 0.2)",
  },
  low: {
    label: "低",
    color: "var(--color-success)",
    bg: "rgba(52, 199, 89, 0.08)",
    border: "rgba(52, 199, 89, 0.2)",
  },
};

const PRIORITY_ORDER: Record<Priority, number> = { high: 0, medium: 1, low: 2 };

export function NextActionsList({ actions }: NextActionsListProps) {
  if (actions.length === 0) {
    return null;
  }

  const sorted = [...actions].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
  );

  return (
    <section>
      <h2
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "22px",
          fontWeight: 600,
          color: "var(--color-fg)",
          marginBottom: "20px",
          letterSpacing: "-0.374px",
        }}
      >
        建議下一步行動
      </h2>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {sorted.map((action, i) => {
          const pCfg = PRIORITY_CONFIG[action.priority];
          return (
            <div
              key={i}
              style={{
                backgroundColor: "var(--color-bg-elevated)",
                borderRadius: "var(--radius-lg)",
                padding: "20px 24px",
                boxShadow: "var(--shadow-card)",
                display: "flex",
                gap: "16px",
                alignItems: "flex-start",
              }}
            >
              {/* Priority badge */}
              <span
                style={{
                  flexShrink: 0,
                  fontFamily: "var(--font-sans)",
                  fontSize: "12px",
                  fontWeight: 600,
                  color: pCfg.color,
                  backgroundColor: pCfg.bg,
                  border: `1px solid ${pCfg.border}`,
                  borderRadius: "var(--radius-pill)",
                  padding: "3px 10px",
                  marginTop: "2px",
                }}
              >
                {pCfg.label}優先
              </span>

              {/* Content */}
              <div style={{ flex: 1 }}>
                <p
                  style={{
                    fontFamily: "var(--font-sans)",
                    fontSize: "15px",
                    fontWeight: 600,
                    color: "var(--color-fg)",
                    marginBottom: "4px",
                    letterSpacing: "-0.374px",
                  }}
                >
                  {ACTION_LABELS[action.action]}
                </p>
                <p
                  style={{
                    fontFamily: "var(--font-sans)",
                    fontSize: "14px",
                    fontWeight: 400,
                    color: "var(--color-fg-muted)",
                    lineHeight: 1.5,
                  }}
                >
                  {action.why}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
