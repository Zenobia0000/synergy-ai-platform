import { Navigate, Outlet } from "react-router-dom";
import { useRole } from "@/contexts/RoleContext";
import { roleHome, type Role } from "@/lib/role";

interface RoleGuardProps {
  require: Role | Role[];
}

export function RoleGuard({ require }: RoleGuardProps) {
  const { role } = useRole();
  const allowed = Array.isArray(require) ? require : [require];

  if (!role) return <Navigate to="/login" replace />;
  if (!allowed.includes(role)) return <Navigate to={roleHome(role)} replace />;

  return <Outlet />;
}
