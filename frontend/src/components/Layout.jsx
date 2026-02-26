import { useEffect, useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

const MOBILE_BREAKPOINT = 1024;

const navBase = [
  { to: "/dashboard", icon: "📊", label: "Dashboard" },
  { to: "/processos", icon: "⚖️", label: "Processos" },
  { to: "/clientes", icon: "👥", label: "Clientes" },
  { to: "/documentos", icon: "📂", label: "Documentos" },
  { to: "/agenda", icon: "📅", label: "Agenda" },
  { to: "/jurisprudencia", icon: "📚", label: "Jurisprudência" },
  { to: "/consulta-tribunais", icon: "🏛️", label: "Consulta Tribunais" },
  { to: "/ia", icon: "🤖", label: "IA Preditiva" },
  { to: "/financeiro", icon: "💰", label: "Financeiro" },
  { to: "/financeiro/cobranca", icon: "🧾", label: "Cobrança & Time" },
];

function getIsMobile() {
  if (typeof window === "undefined") return false;
  return window.innerWidth < MOBILE_BREAKPOINT;
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [isMobile, setIsMobile] = useState(getIsMobile);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [desktopCollapsed, setDesktopCollapsed] = useState(false);

  const isAdmin = user?.papel === "administrador";
  const nav = isAdmin
    ? [...navBase, { to: "/gestao-usuarios", icon: "🛡️", label: "Gestão Usuários" }]
    : navBase;

  useEffect(() => {
    function onResize() {
      const mobile = getIsMobile();
      setIsMobile(mobile);
      if (!mobile) setMobileOpen(false);
    }

    window.addEventListener("resize", onResize);
    onResize();
    return () => window.removeEventListener("resize", onResize);
  }, []);

  function handleSidebarToggle() {
    if (isMobile) {
      setMobileOpen((prev) => !prev);
    } else {
      setDesktopCollapsed((prev) => !prev);
    }
  }

  function handleNavClick() {
    if (isMobile) setMobileOpen(false);
  }

  function handleLogout() {
    logout();
    toast.success("Até logo!");
    if (isMobile) setMobileOpen(false);
    navigate("/login");
  }

  const sidebarWidth = isMobile ? "w-72" : desktopCollapsed ? "w-20" : "w-64";

  return (
    <div className="h-screen bg-gray-50 overflow-hidden">
      <div
        className={`fixed inset-0 z-30 bg-black/45 transition-opacity duration-200 ${
          isMobile && mobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        onClick={() => setMobileOpen(false)}
      />

      <div className="h-full flex">
        <aside
          className={`${isMobile ? "fixed inset-y-0 left-0 z-40" : "relative"} ${sidebarWidth} flex shrink-0 flex-col bg-primary-900 text-white shadow-xl transition-all duration-200 ${
            isMobile && !mobileOpen ? "-translate-x-full" : "translate-x-0"
          }`}
        >
          <div className={`${desktopCollapsed && !isMobile ? "px-3" : "px-6"} py-5 border-b border-primary-800`}>
            <div className={`text-xs font-semibold text-primary-300 uppercase tracking-widest ${desktopCollapsed && !isMobile ? "text-center" : ""}`}>
              Santos Nobre
            </div>
            {(!desktopCollapsed || isMobile) && (
              <div className="text-lg font-bold mt-0.5">Assessoria Jurídica</div>
            )}
          </div>

          <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                title={item.label}
                onClick={handleNavClick}
                className={({ isActive }) =>
                  `flex items-center rounded-lg py-2.5 text-sm font-medium transition-colors ${
                    desktopCollapsed && !isMobile ? "justify-center px-2" : "gap-3 px-3"
                  } ${
                    isActive
                      ? "bg-primary-700 text-white"
                      : "text-primary-200 hover:bg-primary-800 hover:text-white"
                  }`
                }
              >
                <span className="text-lg leading-none">{item.icon}</span>
                {(!desktopCollapsed || isMobile) && <span className="truncate">{item.label}</span>}
              </NavLink>
            ))}
          </nav>

          <div className="px-3 py-4 border-t border-primary-800">
            {(!desktopCollapsed || isMobile) && (
              <div className="text-xs text-primary-300 truncate mb-2">
                {user?.full_name || user?.username || "Usuário"}
              </div>
            )}
            <button
              onClick={handleLogout}
              className={`w-full text-xs text-primary-300 hover:text-white transition-colors ${
                desktopCollapsed && !isMobile ? "text-center" : "text-left"
              }`}
              title="Sair"
            >
              {desktopCollapsed && !isMobile ? "⎋" : "→ Sair"}
            </button>
          </div>
        </aside>

        <main className="flex-1 min-w-0 flex flex-col overflow-hidden">
          <header className="h-14 shrink-0 border-b border-gray-200 bg-white/95 backdrop-blur px-3 md:px-5 flex items-center justify-between">
            <button
              onClick={handleSidebarToggle}
              className="inline-flex items-center justify-center h-9 w-9 rounded-lg border border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
              title="Alternar menu"
            >
              ☰
            </button>
            <div className="text-xs md:text-sm font-medium text-gray-600 truncate ml-3">
              {user?.full_name || user?.username || "Usuário"}
            </div>
          </header>

          <div className="flex-1 overflow-y-auto p-3 sm:p-4 md:p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
