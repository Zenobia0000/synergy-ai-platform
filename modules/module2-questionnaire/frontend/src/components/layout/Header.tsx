import { Link, useNavigate } from "react-router-dom";
import { useRole } from "@/contexts/RoleContext";
import { roleLabel } from "@/lib/role";

export function Header() {
  const { role, clearRole } = useRole();
  const navigate = useNavigate();

  function handleSwitchRole() {
    clearRole();
    navigate("/login");
  }

  return (
    <header className="sticky top-0 z-10 border-b border-border bg-bg-elevated">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <Link
          to="/"
          className="focus-ring font-display text-heading-sm font-semibold text-fg no-underline"
        >
          Synergy AI
        </Link>

        <div className="flex items-center gap-4">
          {role && (
            <span className="rounded-full bg-bg px-3 py-1 text-micro font-medium text-fg-muted">
              {roleLabel(role)}模式
            </span>
          )}
          {role ? (
            <button
              type="button"
              onClick={handleSwitchRole}
              className="focus-ring text-caption font-medium text-link hover:underline"
            >
              切換角色
            </button>
          ) : (
            <Link
              to="/login"
              className="focus-ring text-caption font-medium text-link no-underline hover:underline"
            >
              登入
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
