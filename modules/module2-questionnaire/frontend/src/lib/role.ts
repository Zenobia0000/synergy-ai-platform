export type Role = "user" | "coach";

const STORAGE_KEY = "role";

export function readRole(): Role | null {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  return raw === "user" || raw === "coach" ? raw : null;
}

export function writeRole(role: Role): void {
  window.sessionStorage.setItem(STORAGE_KEY, role);
}

export function clearRoleStorage(): void {
  window.sessionStorage.removeItem(STORAGE_KEY);
  // 故意保留 pending_advice_request / last_advice_result：
  // 教練切換角色時要能看到使用者剛填的結果。
}

export function roleLabel(role: Role): string {
  return role === "user" ? "使用者" : "新手教練";
}

export function roleHome(role: Role): string {
  return role === "user" ? "/u/questionnaire" : "/coach";
}
