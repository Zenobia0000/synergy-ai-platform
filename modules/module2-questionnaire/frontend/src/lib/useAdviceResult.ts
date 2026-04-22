import { useCallback, useEffect, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api";
import type { AdviceResponse } from "@/lib/types";

type State =
  | { kind: "empty" }
  | { kind: "loading" }
  | { kind: "success"; data: AdviceResponse }
  | { kind: "error"; message: string };

const STORAGE_KEY_RESULT = "last_advice_result";
const STORAGE_KEY_REQUEST = "pending_advice_request";

function readCached(): AdviceResponse | null {
  const raw = sessionStorage.getItem(STORAGE_KEY_RESULT);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AdviceResponse;
  } catch {
    return null;
  }
}

function readPendingAnswers(): Record<string, unknown> | null {
  const raw = sessionStorage.getItem(STORAGE_KEY_REQUEST);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return null;
  }
}

/**
 * 封裝 /u/result 與 /coach 共用的資料取得邏輯：
 * 1. 先讀 last_advice_result；有就直接回傳
 * 2. 否則讀 pending_advice_request，呼叫 POST /api/advise
 * 3. 都無則 empty 狀態
 */
export function useAdviceResult(coachLevel: "new" | "senior" = "new") {
  const [state, setState] = useState<State>({ kind: "empty" });

  const run = useCallback(async () => {
    const cached = readCached();
    if (cached) {
      setState({ kind: "success", data: cached });
      return;
    }

    const answers = readPendingAnswers();
    if (!answers) {
      setState({ kind: "empty" });
      return;
    }

    setState({ kind: "loading" });
    try {
      const data = await apiFetch<AdviceResponse>("/advise", {
        method: "POST",
        body: JSON.stringify({ answers, coach_level: coachLevel }),
        headers: { "Content-Type": "application/json" },
      });
      sessionStorage.setItem(STORAGE_KEY_RESULT, JSON.stringify(data));
      setState({ kind: "success", data });
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof ApiError ? err.message : String(err),
      });
    }
  }, [coachLevel]);

  const regenerate = useCallback(async () => {
    sessionStorage.removeItem(STORAGE_KEY_RESULT);
    await run();
  }, [run]);

  useEffect(() => {
    run();
  }, [run]);

  return { state, regenerate };
}
