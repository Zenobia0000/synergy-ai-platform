import { Link } from "react-router-dom";
import { useAdviceResult } from "@/lib/useAdviceResult";
import { SummaryCard } from "@/components/advice/SummaryCard";
import { ProductsGrid } from "@/components/advice/ProductsGrid";

export default function UserResult() {
  const { state, regenerate } = useAdviceResult();

  if (state.kind === "empty") {
    return (
      <section className="mx-auto flex w-full max-w-lg flex-1 items-center justify-center px-4 py-16">
        <div className="text-center">
          <h1 className="font-display text-heading-sm font-semibold text-fg">
            尚未填寫問卷
          </h1>
          <p className="mt-2 text-caption text-fg-muted">
            請先完成問卷，再查看個人化建議。
          </p>
          <Link
            to="/u/questionnaire"
            className="focus-ring mt-6 inline-flex rounded-sm bg-accent px-6 py-2.5 text-body font-normal text-white no-underline hover:bg-accent-hover"
          >
            前往問卷
          </Link>
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

  const { data } = state;
  return (
    <section className="mx-auto w-full max-w-3xl px-6 pb-20 pt-10">
      <header className="mb-8">
        <h1 className="font-display text-heading-md font-bold tracking-tight text-fg">
          您的健康評估結果
        </h1>
        <p className="mt-1 text-caption text-fg-subtle">
          以下為 AI 根據您的問卷回答所產生的個人化建議
        </p>
      </header>

      <div className="flex flex-col gap-8">
        <SummaryCard summary={data.summary} />
        <ProductsGrid products={data.recommended_products} />
      </div>

      <div className="mt-10 flex justify-end gap-3 border-t border-border pt-6">
        <Link
          to="/u/questionnaire"
          className="focus-ring inline-flex rounded-sm border border-border bg-bg-elevated px-5 py-2.5 text-body font-normal text-fg no-underline hover:bg-btn-active"
        >
          再填一次
        </Link>
        <button
          type="button"
          onClick={regenerate}
          className="focus-ring inline-flex rounded-sm bg-accent px-5 py-2.5 text-body font-normal text-white hover:bg-accent-hover"
        >
          重新產生
        </button>
      </div>
    </section>
  );
}
