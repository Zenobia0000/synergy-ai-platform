import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, ApiError } from "@/lib/api";
import type { QuestionnaireSchema, Answers } from "@/lib/types";
import { useRole } from "@/contexts/RoleContext";
import { QuestionnaireForm } from "@/components/questionnaire/QuestionnaireForm";

type LoadState = "loading" | "ready" | "error";

export default function Questionnaire() {
  const navigate = useNavigate();
  const { role } = useRole();
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [schema, setSchema] = useState<QuestionnaireSchema | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");

  async function loadSchema() {
    setLoadState("loading");
    setErrorMsg("");
    try {
      const data = await apiFetch<QuestionnaireSchema>("/questionnaire/schema");
      setSchema(data);
      setLoadState("ready");
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.message : String(err));
      setLoadState("error");
    }
  }

  useEffect(() => {
    loadSchema();
  }, []);

  function handleSubmit(answers: Answers) {
    sessionStorage.setItem("pending_advice_request", JSON.stringify(answers));
    sessionStorage.removeItem("last_advice_result");
    navigate(role === "coach" ? "/coach" : "/u/result");
  }

  if (loadState === "loading") {
    return (
      <section className="flex flex-1 items-center justify-center px-4 py-16">
        <div className="flex flex-col items-center gap-4 text-center">
          <div
            aria-hidden="true"
            className="h-10 w-10 rounded-full border-[3px] border-border border-t-accent"
            style={{ animation: "spin 0.8s linear infinite" }}
          />
          <p className="text-body text-fg-muted">載入問卷中…</p>
        </div>
      </section>
    );
  }

  if (loadState === "error") {
    return (
      <section className="mx-auto flex w-full max-w-lg flex-1 items-center justify-center px-4 py-16">
        <div className="text-center">
          <p className="font-display text-heading-sm font-semibold text-error">
            無法載入問卷
          </p>
          <p className="mt-2 text-caption text-fg-muted">{errorMsg}</p>
          <button
            type="button"
            onClick={loadSchema}
            className="focus-ring mt-6 inline-flex rounded-sm bg-accent px-6 py-2.5 text-body font-normal text-white hover:bg-accent-hover"
          >
            重試
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="flex-1">
      {schema && <QuestionnaireForm schema={schema} onSubmit={handleSubmit} />}
    </section>
  );
}
