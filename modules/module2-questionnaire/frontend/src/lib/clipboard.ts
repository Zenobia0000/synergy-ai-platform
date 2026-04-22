/**
 * 複製文字到剪貼板的工具函式
 * 優先使用 navigator.clipboard API（需安全上下文）
 * 降級到隱藏 textarea + document.execCommand("copy")
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  // SSR guard
  if (typeof navigator === "undefined") {
    return false;
  }

  // 優先：Clipboard API（現代瀏覽器 / HTTPS）
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // 可能因權限被拒，繼續嘗試 fallback
    }
  }

  // Fallback：隱藏 textarea + execCommand
  if (typeof document === "undefined") {
    return false;
  }

  try {
    const textarea = document.createElement("textarea");
    textarea.value = text;

    // 防止頁面捲動
    textarea.style.position = "fixed";
    textarea.style.top = "0";
    textarea.style.left = "0";
    textarea.style.width = "1px";
    textarea.style.height = "1px";
    textarea.style.opacity = "0";
    textarea.style.pointerEvents = "none";
    textarea.setAttribute("readonly", "");
    textarea.setAttribute("aria-hidden", "true");

    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();

    const success = document.execCommand("copy");
    document.body.removeChild(textarea);
    return success;
  } catch {
    return false;
  }
}
