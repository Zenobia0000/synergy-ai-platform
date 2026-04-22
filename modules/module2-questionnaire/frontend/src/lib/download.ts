/**
 * 將文字內容以 .md 檔案下載到使用者裝置
 * 使用 Blob + URL.createObjectURL（僅瀏覽器端可用）
 */
export function downloadMarkdown(filename: string, content: string): void {
  if (typeof document === "undefined") {
    return;
  }

  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.style.display = "none";

  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);

  // 釋放記憶體
  URL.revokeObjectURL(url);
}

/**
 * 以今日日期產生預設檔名
 * 格式：synergy-advice-YYYY-MM-DD.md
 */
export function buildDefaultFilename(): string {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `synergy-advice-${yyyy}-${mm}-${dd}.md`;
}
