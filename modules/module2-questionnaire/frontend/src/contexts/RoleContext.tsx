import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { clearRoleStorage, readRole, writeRole, type Role } from "@/lib/role";

interface RoleContextValue {
  role: Role | null;
  setRole: (role: Role) => void;
  clearRole: () => void;
}

const RoleContext = createContext<RoleContextValue | null>(null);

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<Role | null>(() => readRole());

  const setRole = useCallback((next: Role) => {
    writeRole(next);
    setRoleState(next);
  }, []);

  const clearRole = useCallback(() => {
    clearRoleStorage();
    setRoleState(null);
  }, []);

  const value = useMemo<RoleContextValue>(
    () => ({ role, setRole, clearRole }),
    [role, setRole, clearRole],
  );

  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>;
}

export function useRole(): RoleContextValue {
  const ctx = useContext(RoleContext);
  if (!ctx) throw new Error("useRole must be used within RoleProvider");
  return ctx;
}
