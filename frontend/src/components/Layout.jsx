import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

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
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.papel === "administrador";

  const nav = isAdmin
    ? [...navBase, { to: "/gestao-usuarios", icon: "🛡️", label: "Gestão Usuários" }]
    : navBase;

  function handleLogout() {
    logout();
    toast.success("Até logo!");
    navigate("/login");
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 flex flex-col bg-primary-900 text-white shrink-0">
        <div className="px-6 py-5 border-b border-primary-800">
          <div className="text-xs font-semibold text-primary-300 uppercase tracking-widest">Santos Nobre</div>
          <div className="text-lg font-bold mt-0.5">Assessoria Jurídica</div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary-700 text-white"
                    : "text-primary-200 hover:bg-primary-800 hover:text-white"
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-4 border-t border-primary-800">
          <div className="text-xs text-primary-300 truncate mb-2">
            {user?.full_name || user?.username || "Usuário"}
          </div>
          <button onClick={handleLogout} className="w-full text-xs text-primary-300 hover:text-white transition-colors text-left">
            → Sair
          </button>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
