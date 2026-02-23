import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";

function StatCard({ icon, label, value, color = "blue", onClick }) {
  const colors = {
    blue: "bg-blue-50 text-blue-700 border-blue-200",
    green: "bg-green-50 text-green-700 border-green-200",
    yellow: "bg-yellow-50 text-yellow-700 border-yellow-200",
    red: "bg-red-50 text-red-700 border-red-200",
  };
  return (
    <div
      onClick={onClick}
      className={`card border ${colors[color]} cursor-pointer hover:shadow-md transition-shadow`}
    >
      <div className="text-3xl mb-2">{icon}</div>
      <div className="text-3xl font-bold">{value ?? "—"}</div>
      <div className="text-sm mt-1 font-medium">{label}</div>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({});
  const [eventos, setEventos] = useState([]);
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/usuarios/dashboard/").catch(() => ({ data: {} })),
      api.get("/eventos/prazos-proximos/").catch(() => ({ data: [] })),
      api.get("/processos/?limit=5").catch(() => ({ data: { results: [] } })),
    ]).then(([dash, ev, proc]) => {
      setStats(dash.data);
      setEventos(Array.isArray(ev.data) ? ev.data : ev.data?.results || []);
      setProcessos(proc.data?.results || proc.data || []);
      setLoading(false);
    });
  }, []);

  const hora = new Date().getHours();
  const saudacao = hora < 12 ? "Bom dia" : hora < 18 ? "Boa tarde" : "Boa noite";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {saudacao}, {user?.first_name || user?.username || "Advogado"} 👋
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          {new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
        </p>
      </div>

      {/* Cards de estatísticas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon="⚖️" label="Processos Ativos" value={stats.processos_ativos} color="blue" onClick={() => navigate("/processos")} />
        <StatCard icon="👥" label="Total de Clientes" value={stats.total_clientes} color="green" onClick={() => navigate("/clientes")} />
        <StatCard icon="📅" label="Eventos Hoje" value={stats.eventos_hoje} color="yellow" onClick={() => navigate("/agenda")} />
        <StatCard icon="⚠️" label="Prazos Próximos" value={stats.prazos_proximos} color="red" onClick={() => navigate("/agenda")} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Prazos próximos */}
        <div className="card">
          <h2 className="text-base font-semibold text-gray-800 mb-4">📅 Próximos Prazos</h2>
          {loading ? (
            <p className="text-sm text-gray-400">Carregando...</p>
          ) : eventos.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhum prazo próximo</p>
          ) : (
            <ul className="space-y-2">
              {eventos.slice(0, 5).map((ev) => (
                <li key={ev.id} className="flex justify-between items-start text-sm border-b border-gray-100 pb-2">
                  <div>
                    <div className="font-medium text-gray-800">{ev.titulo}</div>
                    <div className="text-xs text-gray-500">{ev.processo_numero}</div>
                  </div>
                  <span className="badge-red text-xs shrink-0 ml-2">
                    {ev.data_inicio ? new Date(ev.data_inicio).toLocaleDateString("pt-BR") : ev.data}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Processos recentes */}
        <div className="card">
          <h2 className="text-base font-semibold text-gray-800 mb-4">⚖️ Processos Recentes</h2>
          {loading ? (
            <p className="text-sm text-gray-400">Carregando...</p>
          ) : processos.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhum processo cadastrado</p>
          ) : (
            <ul className="space-y-2">
              {processos.slice(0, 5).map((p) => (
                <li
                  key={p.id}
                  className="flex justify-between items-center text-sm border-b border-gray-100 pb-2 cursor-pointer hover:text-primary-600"
                  onClick={() => navigate(`/processos/${p.id}`)}
                >
                  <div>
                    <div className="font-medium">{p.numero}</div>
                    <div className="text-xs text-gray-500">{p.cliente_nome}</div>
                  </div>
                  <StatusBadge status={p.status} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const map = {
    em_andamento: "badge-blue",
    suspenso: "badge-yellow",
    finalizado: "badge-green",
    arquivado: "badge-gray",
  };
  const labels = { em_andamento: "Em andamento", suspenso: "Suspenso", finalizado: "Finalizado", arquivado: "Arquivado" };
  return <span className={map[status] || "badge-gray"}>{labels[status] || status}</span>;
}
