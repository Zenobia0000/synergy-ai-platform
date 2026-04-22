import { useState, useCallback } from "react";
import type { AdviceResponse, OverallLevel } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { copyToClipboard } from "@/lib/clipboard";
import { buildFullAdviceMarkdown } from "@/lib/markdown";
import { downloadMarkdown, buildDefaultFilename } from "@/lib/download";
import { SummaryCard } from "./SummaryCard";
import { ProductsGrid } from "./ProductsGrid";
import { ScriptsList } from "./ScriptsList";
import { NextActionsList } from "./NextActionsList";

interface AdviceViewProps {
  response: AdviceResponse;
  onBack: () => void;
  onRegenerate: () => void;
}

const LEVEL_CONFIG: Record<
  OverallLevel,
  { label: string; color: string; bg: string; border: string }
> = {
  low: {
    label: "低風險",
    color: "var(--color-success)",
    bg: "rgba(52, 199, 89, 0.08)",
    border: "rgba(52, 199, 89, 0.25)",
  },
  medium: {
    label: "中度風險",
    color: "var(--color-warning)",
    bg: "rgba(255, 159, 10, 0.08)",
    border: "rgba(255, 159, 10, 0.25)",
  },
  high: {
    label: "高風險",
    color: "var(--color-error)",
    bg: "rgba(255, 59, 48, 0.08)",
    border: "rgba(255, 59, 48, 0.25)",
  },
};

type CopyAllState = "idle" | "success" | "error";

export function AdviceView({ response, onBack, onRegenerate }: AdviceViewProps) {
  const level = response.summary.overall_level;
  const levelCfg = LEVEL_CONFIG[level];

  const [copyAllState, setCopyAllState] = useState<CopyAllState>("idle");

  const handleCopyAll = useCallback(async () => {
    const markdown = buildFullAdviceMarkdown(response);
    const ok = await copyToClipboard(markdown);
    setCopyAllState(ok ? "success" : "error");
    setTimeout(() => setCopyAllState("idle"), 2500);
  }, [response]);

  const handleDownload = useCallback(() => {
    const markdown = buildFullAdviceMarkdown(response);
    const filename = buildDefaultFilename();
    downloadMarkdown(filename, markdown);
  }, [response]);

  const copyAllLabel =
    copyAllState === "success"
      ? "已複製"
      : copyAllState === "error"
      ? "複製失敗"
      : "複製全部";

  return (
    <div
      style={{
        maxWidth: "800px",
        margin: "0 auto",
        padding: "40px 24px 80px",
      }}
    >
      {/* Page header */}
      <div style={{ marginBottom: "32px" }}>
        {/* Title row: heading + level badge + export actions */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            flexWrap: "wrap",
            marginBottom: "8px",
          }}
        >
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "28px",
              fontWeight: 700,
              color: "var(--color-fg)",
              letterSpacing: "-0.374px",
              margin: 0,
              flex: "1 1 auto",
            }}
          >
            您的健康評估建議
          </h1>

          <span
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "13px",
              fontWeight: 600,
              color: levelCfg.color,
              backgroundColor: levelCfg.bg,
              border: `1px solid ${levelCfg.border}`,
              borderRadius: "var(--radius-pill)",
              padding: "4px 12px",
              flexShrink: 0,
            }}
          >
            {levelCfg.label}
          </span>

          {/* Export toolbar */}
          <div
            style={{
              display: "flex",
              gap: "8px",
              alignItems: "center",
              flexShrink: 0,
            }}
          >
            <Button
              variant="primary"
              size="sm"
              onClick={handleCopyAll}
              aria-label="複製全部建議為 Markdown"
            >
              {copyAllLabel}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleDownload}
              aria-label="下載建議為 Markdown 檔案"
            >
              下載 Markdown
            </Button>
          </div>
        </div>

        <p
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "15px",
            color: "var(--color-fg-subtle)",
            margin: 0,
          }}
        >
          以下為 AI 根據您的問卷回答所產生的個人化建議
        </p>
      </div>

      {/* Four sections */}
      <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
        <SummaryCard summary={response.summary} />
        <ProductsGrid products={response.recommended_products} />
        <ScriptsList scripts={response.sales_scripts} />
        <NextActionsList actions={response.next_actions} />
      </div>

      {/* Footer actions */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          justifyContent: "flex-end",
          marginTop: "40px",
          paddingTop: "24px",
          borderTop: "1px solid var(--color-border)",
          flexWrap: "wrap",
        }}
      >
        <Button variant="secondary" size="md" onClick={onBack}>
          返回問卷
        </Button>
        <Button variant="primary" size="md" onClick={onRegenerate}>
          重新產生
        </Button>
      </div>
    </div>
  );
}
