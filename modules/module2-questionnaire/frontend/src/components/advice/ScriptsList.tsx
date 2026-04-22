import { useState, useCallback } from "react";
import type { SalesScript, ScriptScenario } from "@/lib/types";
import { copyToClipboard } from "@/lib/clipboard";
import { buildScriptMarkdown } from "@/lib/markdown";

interface ScriptsListProps {
  scripts: SalesScript[];
}

const SCENARIO_CONFIG: Record<
  ScriptScenario,
  { label: string; icon: string }
> = {
  opening: { label: "開場白", icon: "👋" },
  objection: { label: "異議處理", icon: "🤝" },
  closing: { label: "收尾成交", icon: "✅" },
  follow_up: { label: "後續跟進", icon: "📩" },
};

type CopyState = "idle" | "success" | "error";

interface ScriptCardProps {
  script: SalesScript;
  index: number;
}

function ScriptCard({ script, index }: ScriptCardProps) {
  const [copyState, setCopyState] = useState<CopyState>("idle");

  const handleCopy = useCallback(async () => {
    const markdown = buildScriptMarkdown(script);
    const ok = await copyToClipboard(markdown);
    setCopyState(ok ? "success" : "error");
    setTimeout(() => setCopyState("idle"), 2000);
  }, [script]);

  const config = SCENARIO_CONFIG[script.scenario];

  const copyLabel =
    copyState === "success"
      ? "已複製"
      : copyState === "error"
      ? "複製失敗，請手動選取"
      : "複製";

  const copyColor =
    copyState === "success"
      ? "var(--color-success)"
      : copyState === "error"
      ? "var(--color-error)"
      : "var(--color-link)";

  const copyBorder =
    copyState === "success"
      ? "var(--color-success)"
      : copyState === "error"
      ? "var(--color-error)"
      : "var(--color-link)";

  return (
    <div
      key={index}
      style={{
        backgroundColor: "var(--color-bg-elevated)",
        borderRadius: "var(--radius-lg)",
        padding: "24px",
        boxShadow: "var(--shadow-card)",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "16px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "20px" }}>{config.icon}</span>
          <span
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "15px",
              fontWeight: 600,
              color: "var(--color-fg)",
              letterSpacing: "-0.374px",
            }}
          >
            {config.label}
          </span>
        </div>
        <button
          onClick={handleCopy}
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "13px",
            fontWeight: 500,
            color: copyColor,
            backgroundColor: "transparent",
            border: `1px solid ${copyBorder}`,
            borderRadius: "var(--radius-sm)",
            padding: "4px 12px",
            cursor: "pointer",
            transition: "color 0.15s ease, border-color 0.15s ease",
            whiteSpace: "nowrap",
          }}
          aria-label={`複製${config.label}話術`}
        >
          {copyLabel}
        </button>
      </div>

      {/* Script content */}
      <p
        style={{
          fontFamily: "var(--font-sans)",
          fontSize: "15px",
          fontWeight: 400,
          color: "var(--color-fg)",
          lineHeight: 1.7,
          whiteSpace: "pre-wrap",
        }}
      >
        {script.script}
      </p>

      {/* Taboo warning */}
      {script.taboo && (
        <div
          style={{
            marginTop: "16px",
            padding: "12px 16px",
            backgroundColor: "rgba(255, 159, 10, 0.08)",
            border: "1px solid rgba(255, 159, 10, 0.3)",
            borderRadius: "var(--radius-md)",
            display: "flex",
            gap: "8px",
            alignItems: "flex-start",
          }}
        >
          <span style={{ fontSize: "15px", flexShrink: 0 }}>⚠️</span>
          <div>
            <p
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "12px",
                fontWeight: 600,
                color: "var(--color-warning)",
                marginBottom: "2px",
                textTransform: "uppercase",
                letterSpacing: "0.3px",
              }}
            >
              禁忌提醒
            </p>
            <p
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "13px",
                fontWeight: 400,
                color: "var(--color-fg-muted)",
                lineHeight: 1.5,
              }}
            >
              {script.taboo}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export function ScriptsList({ scripts }: ScriptsListProps) {
  if (scripts.length === 0) {
    return null;
  }

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
        銷售話術建議
      </h2>

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {scripts.map((script, i) => (
          <ScriptCard key={i} script={script} index={i} />
        ))}
      </div>
    </section>
  );
}
