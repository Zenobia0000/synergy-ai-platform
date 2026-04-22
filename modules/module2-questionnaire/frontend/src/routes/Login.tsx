import { useNavigate } from "react-router-dom";
import { useRole } from "@/contexts/RoleContext";
import { roleHome, type Role } from "@/lib/role";

interface RoleOption {
  role: Role;
  title: string;
  subtitle: string;
  bullets: string[];
}

const ROLE_OPTIONS: RoleOption[] = [
  {
    role: "user",
    title: "一般使用者",
    subtitle: "填寫健康問卷，取得個人化建議",
    bullets: [
      "填寫健康評估問卷",
      "取得健康研判摘要",
      "看到推薦產品與符合度",
    ],
  },
  {
    role: "coach",
    title: "新手教練",
    subtitle: "檢視客戶資料與完整行銷建議",
    bullets: [
      "檢視客戶問卷結果",
      "取得推薦產品組合",
      "銷售話術與下一步行動",
      "匯出 Markdown 建議",
    ],
  },
];

export default function Login() {
  const navigate = useNavigate();
  const { setRole } = useRole();

  function handleSelect(role: Role) {
    setRole(role);
    navigate(roleHome(role), { replace: true });
  }

  return (
    <section className="mx-auto w-full max-w-4xl px-4 py-16">
      <header className="mb-12 text-center">
        <h1 className="font-display text-heading-lg font-semibold tracking-tight text-fg">
          選擇角色進入
        </h1>
        <p className="mt-3 text-body text-fg-muted">
          POC 階段尚未接真實認證，請選擇角色以體驗不同流程
        </p>
      </header>

      <div className="grid gap-6 md:grid-cols-2">
        {ROLE_OPTIONS.map((opt) => (
          <button
            key={opt.role}
            type="button"
            onClick={() => handleSelect(opt.role)}
            className="focus-ring group flex flex-col gap-4 rounded-xl bg-bg-elevated p-8 text-left shadow-card transition-transform duration-150 hover:-translate-y-0.5"
          >
            <div>
              <h2 className="font-display text-heading-sm font-bold text-fg">
                {opt.title}
              </h2>
              <p className="mt-1 text-caption text-fg-muted">{opt.subtitle}</p>
            </div>
            <ul className="flex flex-col gap-2 text-caption text-fg-muted">
              {opt.bullets.map((b) => (
                <li key={b} className="flex items-start gap-2">
                  <span
                    aria-hidden="true"
                    className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent"
                  />
                  {b}
                </li>
              ))}
            </ul>
            <span className="mt-auto inline-flex items-center gap-1 text-caption font-semibold text-link">
              進入
              <span aria-hidden="true" className="transition-transform group-hover:translate-x-0.5">→</span>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
