interface QuestionnaireProgressProps {
  currentIndex: number;
  total: number;
  sectionTitles: string[];
}

export function QuestionnaireProgress({
  currentIndex,
  total,
  sectionTitles,
}: QuestionnaireProgressProps) {
  const percent = total > 0 ? Math.round(((currentIndex + 1) / total) * 100) : 0;
  const currentTitle = sectionTitles[currentIndex] ?? "";

  return (
    <div
      style={{
        marginBottom: "32px",
      }}
    >
      {/* Section label */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: "10px",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "14px",
            fontWeight: 600,
            lineHeight: 1.29,
            letterSpacing: "-0.224px",
            color: "var(--color-fg)",
          }}
        >
          第 {currentIndex + 1} / {total} 段：{currentTitle}
        </span>
        <span
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "12px",
            fontWeight: 400,
            lineHeight: 1.33,
            letterSpacing: "-0.12px",
            color: "var(--color-fg-subtle)",
          }}
        >
          {percent}%
        </span>
      </div>

      {/* Progress bar */}
      <div
        role="progressbar"
        aria-valuenow={currentIndex + 1}
        aria-valuemin={1}
        aria-valuemax={total}
        aria-label={`問卷進度 ${currentIndex + 1} / ${total}`}
        style={{
          width: "100%",
          height: "4px",
          backgroundColor: "var(--color-border)",
          borderRadius: "var(--radius-pill)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${percent}%`,
            backgroundColor: "var(--color-accent)",
            borderRadius: "var(--radius-pill)",
            transition: `width var(--duration-base) var(--ease-out)`,
          }}
        />
      </div>
    </div>
  );
}
