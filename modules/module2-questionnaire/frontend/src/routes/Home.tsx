import { Link } from "react-router-dom";
import { useRole } from "@/contexts/RoleContext";
import { roleHome, roleLabel } from "@/lib/role";

export default function Home() {
  const { role } = useRole();

  return (
    <section className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-4 py-16">
      <header className="mb-12 text-center">
        <h1 className="font-display text-hero font-semibold tracking-tight text-fg">
          Synergy Questionnaire AI
        </h1>
        <p className="mt-4 font-sans text-heading-sm font-normal text-fg-muted">
          健康評估 × 行銷建議 POC
        </p>
      </header>

      <div className="flex flex-col items-center gap-3 text-center">
        {role ? (
          <>
            <p className="text-caption text-fg-muted">
              目前為{roleLabel(role)}模式
            </p>
            <Link
              to={roleHome(role)}
              className="focus-ring inline-flex items-center gap-2 rounded-pill bg-fg px-8 py-3 text-body font-normal text-white no-underline transition-opacity hover:opacity-90"
            >
              {role === "user" ? "開始問卷" : "進入教練面板"}
            </Link>
          </>
        ) : (
          <Link
            to="/login"
            className="focus-ring inline-flex items-center gap-2 rounded-pill bg-accent px-8 py-3 text-body font-normal text-white no-underline transition-colors hover:bg-accent-hover"
          >
            前往登入
          </Link>
        )}
      </div>

      <p className="mt-12 text-center text-micro text-fg-subtle">
        POC 開發中 · WBS 任務 5.3 · Apple Design System
      </p>
    </section>
  );
}
