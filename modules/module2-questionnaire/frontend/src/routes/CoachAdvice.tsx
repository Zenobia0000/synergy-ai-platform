import { Link, useNavigate } from "react-router-dom";
import { useAdviceResult } from "@/lib/useAdviceResult";
import { AdviceView } from "@/components/advice/AdviceView";

export default function CoachAdvice() {
  const navigate = useNavigate();
  const { state, regenerate } = useAdviceResult();

  if (state.kind === "empty") {
    return (
      <section className="mx-auto flex w-full max-w-xl flex-1 items-center justify-center px-4 py-16">
        <div className="text-center">
          <h1 className="font-display text-heading-sm font-semibold text-fg">
            目前沒有問卷結果
          </h1>
          <p className="mt-2 text-caption text-fg-muted">
            請先以「使用者」身份填寫一份問卷，再回到教練面板查看完整建議。
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link
              to="/u/questionnaire"
              className="focus-ring inline-flex rounded-sm bg-accent px-5 py-2.5 text-body font-normal text-white no-underline hover:bg-accent-hover"
            >
              前往問卷
            </Link>
          </div>
        </div>
      </section>
    );
  }

  if (state.kind === "loading") {
    return (
      <section className="flex flex-1 items-center justify-center px-4 py-16">
        <div className="flex flex-col items-center gap-4 text-center">
          <div
            aria-hidden="true"
            className="h-11 w-11 rounded-full border-[3px] border-border border-t-accent"
            style={{ animation: "spin 0.8s linear infinite" }}
          />
          <p className="text-body text-fg-muted">產生建議中…（約 10–30 秒）</p>
        </div>
      </section>
    );
  }

  if (state.kind === "error") {
    return (
      <section className="mx-auto flex w-full max-w-lg flex-1 items-center justify-center px-4 py-16">
        <div className="text-center">
          <h1 className="font-display text-heading-sm font-semibold text-error">
            產生建議失敗
          </h1>
          <p className="mt-2 text-caption text-fg-muted">{state.message}</p>
          <div className="mt-6 flex justify-center gap-3">
            <Link
              to="/u/questionnaire"
              className="focus-ring inline-flex rounded-sm border border-border bg-bg-elevated px-5 py-2.5 text-body font-normal text-fg no-underline hover:bg-btn-active"
            >
              返回問卷
            </Link>
            <button
              type="button"
              onClick={regenerate}
              className="focus-ring inline-flex rounded-sm bg-accent px-5 py-2.5 text-body font-normal text-white hover:bg-accent-hover"
            >
              重試
            </button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <AdviceView
      response={state.data}
      onBack={() => navigate("/u/questionnaire")}
      onRegenerate={regenerate}
    />
  );
}
