import { LogOut, Package, Plug } from "lucide-react";
import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";

const navItemClasses = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive
      ? "bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300"
      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
  }`;

export function AppLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    void navigate("/login");
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <span className="text-lg font-semibold text-brand-700 dark:text-brand-400">tap</span>
            <nav className="flex items-center gap-1">
              <NavLink to="/" className={navItemClasses} end>
                <Package className="size-4" aria-hidden="true" />
                Pacchi
              </NavLink>
              <NavLink to="/settings/connections" className={navItemClasses}>
                <Plug className="size-4" aria-hidden="true" />
                Connessioni
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {user && (
              <span className="text-sm text-slate-500 dark:text-slate-400">{user.email}</span>
            )}
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
            >
              <LogOut className="size-4" aria-hidden="true" />
              Esci
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
    </div>
  );
}
