import type { HealthAssessmentSummary } from "@/lib/types";

interface SummaryCardProps {
  summary: HealthAssessmentSummary;
}

export function SummaryCard({ summary }: SummaryCardProps) {
  return (
    <section
      style={{
        backgroundColor: "var(--color-bg-elevated)",
        borderRadius: "var(--radius-lg)",
        padding: "32px",
        boxShadow: "var(--shadow-card)",
      }}
    >
      <h2
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "22px",
          fontWeight: 600,
          color: "var(--color-fg)",
          marginBottom: "16px",
          letterSpacing: "-0.374px",
        }}
      >
        健康評估摘要
      </h2>

      <p
        style={{
          fontFamily: "var(--font-sans)",
          fontSize: "17px",
          fontWeight: 400,
          lineHeight: 1.6,
          color: "var(--color-fg)",
          marginBottom: "24px",
        }}
      >
        {summary.narrative}
      </p>

      {summary.key_risks.length > 0 && (
        <div style={{ marginBottom: "24px" }}>
          <p
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "13px",
              fontWeight: 600,
              color: "var(--color-fg-subtle)",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              marginBottom: "10px",
            }}
          >
            主要風險
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {summary.key_risks.map((risk, i) => (
              <span
                key={i}
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "13px",
                  fontWeight: 500,
                  color: "var(--color-error)",
                  backgroundColor: "rgba(255, 59, 48, 0.08)",
                  border: "1px solid rgba(255, 59, 48, 0.2)",
                  borderRadius: "var(--radius-pill)",
                  padding: "4px 12px",
                }}
              >
                {risk}
              </span>
            ))}
          </div>
        </div>
      )}

      {summary.disclaimers.length > 0 && (
        <div
          style={{
            borderTop: "1px solid var(--color-border)",
            paddingTop: "16px",
          }}
        >
          {summary.disclaimers.map((d, i) => (
            <p
              key={i}
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "12px",
                fontWeight: 400,
                color: "var(--color-fg-subtle)",
                lineHeight: 1.5,
                margin: i > 0 ? "6px 0 0 0" : "0",
              }}
            >
              {d}
            </p>
          ))}
        </div>
      )}
    </section>
  );
}
