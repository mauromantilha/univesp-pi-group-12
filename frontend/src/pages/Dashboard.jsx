import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { differenceInCalendarDays, parseISO, format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";

function StatCard({ icon, label, value, color = "blue", onClick }) {
  const colors = {
    blue:   "bg-blue-50 text-blue-700 border-blue-200",
    green:  "bg-green-50 text-green-700 border-green-200",
    yellow: "bg-yellow-50 text-yellow-700 border-yellow-200",
    red:    "bg-red-50 text-red-700 border-red-200",
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

function PrazoItem({ ev }) {
  if (!ev.data) return null;
  const days = differenceInCalendarDays(parseISO(ev.data), new Date());
  let bg, dot, label;
  if (days < 0)        { bg = "border-red-400 bg-red-50";        dot = "bg-red-500";    label = `Vencido há ${Math.abs(days)}d`; }
  else if (days === 0) { bg = "border-red-400 bg-red-50";        dot = "bg-red-500";    label = "HOJE"; }
  else if (days <= 3)  { bg = "border-orange-400 bg-orange-50";  dot = "bg-orange-500"; label = `${days}d`; }
  else                 { bg = "border-yellow-400 bg-yellow-50";  dot = "bg-yellow-500"; label = `${days}d`; }

  // Build a display string from date + optional time
  const dataHora = ev.hora
    ? format(parseISO(`${ev.data}T${ev.hora}`), "dd/MM HH:mm", { locale: ptBR })
    : format(parseISO(ev.data), "dd/MM", { locale: ptBR });

  return (
    <li className={`flex justify-between items-start text-sm border-l-4 rounded-r-lg px-3 py-2 ${bg}`}>
      <div className="flex items-start gap-2 min-w-0">
        <span className={`mt-1 w-2 h-2 rounded-full shrink-0 ${dot}`}/>
        <div className="min-w-0">
          <div className="font-medium text-gray-800 truncate">{ev.titulo}</div>
          {ev.processo_numero && <div className="text-xs text-gray-500 font-mono">{ev.processo_numero}</div>}
        </div>
      </div>
      <div className="text-right shrink-0 ml-2">
        <div className={`font-bold text-xs ${days <= 0 ? "text-red-700" : days <= 3 ? "text-orange-700" : "text-yellow-700"}`}>{label}</div>
        <div className="text-xs text-gray-400">{dataHora}</div>
      </div>
    </li>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats]         = useState({});
  const [eventos, setEventos]     = useState([]);
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading]     = useState(true);

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

  // Segregar prazos por urgência para o alerta vermelho no topo
  const prazosUrgentes = eventos.filter((ev) => {
    if (!ev.data) return false;
    const days = differenceInCalendarDays(parseISO(ev.data), new Date());
    return days <= 1 && ev.status !== "concluido" && ev.status !== "cancelado";
  });

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

      {/* Alerta de prazos urgentes (hoje ou atrasados) */}
      {prazosUrgentes.length > 0 && (
        <div className="rounded-xl border-2 border-red-400 bg-red-50 p-4">
          <div className="flex items-center gap-2 font-bold text-red-700 mb-2">
            <span className="text-xl">🚨</span>
            <span>{prazosUrgentes.length} prazo(s) URGENTE(S) — hoje ou vencido(s)!</span>
          </div>
          <div className="space-y-1">
            {prazosUrgentes.map((ev) => (
              <div key={ev.id} className="flex justify-between text-sm text-red-700">
                <span className="font-medium">• {ev.titulo}</span>
                <span className="font-bold">
                  {ev.data
                    ? ev.hora
                      ? format(parseISO(`${ev.data}T${ev.hora}`), "dd/MM HH:mm", { locale: ptBR })
                      : format(parseISO(ev.data), "dd/MM", { locale: ptBR })
                    : "–"}
                </span>
              </div>
            ))}
          </div>
          <button onClick={() => navigate("/agenda")} className="mt-2 text-xs text-red-600 underline">
            Ver todos na Agenda →
          </button>
        </div>
      )}

      {/* Cards de estatísticas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon="⚖️" label="Processos Ativos"  value={stats.processos_ativos} color="blue"   onClick={() => navigate("/processos")} />
        <StatCard icon="👥" label="Total de Clientes" value={stats.total_clientes}   color="green"  onClick={() => navigate("/clientes")} />
        <StatCard icon="📅" label="Eventos Hoje"      value={stats.eventos_hoje}     color="yellow" onClick={() => navigate("/agenda")} />
        <StatCard icon="⚠️" label="Prazos Próximos"   value={stats.prazos_proximos}  color="red"    onClick={() => navigate("/agenda")} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Prazos próximos com urgência */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-800">⏰ Próximos Prazos</h2>
            <button onClick={() => navigate("/agenda")} className="text-xs text-primary-600 hover:underline">Ver todos →</button>
          </div>
          {loading ? (
            <p className="text-sm text-gray-400">Carregando...</p>
          ) : eventos.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhum prazo próximo 🎉</p>
          ) : (
            <ul className="space-y-2">
              {eventos.slice(0, 7).map((ev) => <PrazoItem key={ev.id} ev={ev} />)}
            </ul>
          )}
        </div>

        {/* Processos recentes */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-800">⚖️ Processos Recentes</h2>
            <button onClick={() => navigate("/processos")} className="text-xs text-primary-600 hover:underline">Ver todos →</button>
          </div>
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
                    <div className="font-medium font-mono text-xs">{p.numero}</div>
                    <div className="text-xs text-gray-500">{p.cliente_nome}</div>
                    {p.tipo_nome && <div className="text-xs text-gray-400">{p.tipo_nome}</div>}
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
  const map    = { em_andamento:"badge-blue", suspenso:"badge-yellow", finalizado:"badge-green", arquivado:"badge-gray" };
  const labels = { em_andamento:"Em andamento", suspenso:"Suspenso", finalizado:"Finalizado", arquivado:"Arquivado" };
  return <span className={map[status] || "badge-gray"}>{labels[status] || status}</span>;
}
