import { useState, useEffect, useCallback } from "react";
import { format, parseISO, isPast, isToday } from "date-fns";
import { ptBR } from "date-fns/locale";
import api from "../api/axios";
import toast from "react-hot-toast";

const TIPOS = ["audiencia","prazo","reuniao","pericia","diligencia","outros"];
const STATUS = ["pendente","realizado","cancelado"];

function badgeEvento(tipo) {
  const m = { audiencia:"badge-blue", prazo:"badge-red", reuniao:"badge-green", pericia:"badge-yellow", diligencia:"badge-yellow", outros:"badge-gray" };
  return m[tipo] || "badge-gray";
}
function badgeStatus(s) {
  const m = { pendente:"badge-yellow", realizado:"badge-green", cancelado:"badge-red" };
  return m[s] || "badge-gray";
}

export default function Agenda() {
  const [eventos, setEventos] = useState([]);
  const [prazos, setPrazos] = useState([]);
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterTipo, setFilterTipo] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ titulo:"", tipo:"audiencia", data_inicio:"", data_fim:"", processo:"", descricao:"", local:"" });

  const fetchAll = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filterTipo) params.append("tipo", filterTipo);
    if (filterStatus) params.append("status", filterStatus);
    Promise.all([
      api.get(`/eventos/?${params}`),
      api.get("/eventos/prazos-proximos/"),
      api.get("/processos/?limit=100"),
    ]).then(([ev, pr, proc]) => {
      setEventos(ev.data?.results || ev.data || []);
      setPrazos(pr.data?.results || pr.data || []);
      setProcessos(proc.data?.results || proc.data || []);
    }).finally(() => setLoading(false));
  }, [filterTipo, filterStatus]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      const payload = {...form};
      if (!payload.data_fim) delete payload.data_fim;
      if (!payload.processo) delete payload.processo;
      await api.post("/eventos/", payload);
      toast.success("Evento criado!");
      setShowModal(false);
      fetchAll();
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data).slice(0,140) : "Erro ao salvar");
    }
  }

  async function marcarRealizado(id) {
    try {
      await api.patch(`/eventos/${id}/`, { status: "realizado" });
      toast.success("Marcado como realizado");
      fetchAll();
    } catch { toast.error("Erro ao atualizar"); }
  }

  function rowClass(ev) {
    if (ev.status === "realizado") return "opacity-50";
    if (ev.tipo === "prazo" && isPast(parseISO(ev.data_inicio)) && ev.status === "pendente") return "bg-red-50";
    if (isToday(parseISO(ev.data_inicio))) return "bg-yellow-50";
    return "";
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">📅 Agenda</h1>
        <button onClick={() => { setForm({ titulo:"", tipo:"audiencia", data_inicio:"", data_fim:"", processo:"", descricao:"", local:"" }); setShowModal(true); }} className="btn-primary">+ Novo Evento</button>
      </div>

      {prazos.length > 0 && (
        <div className="card border-l-4 border-red-500 bg-red-50">
          <h2 className="font-semibold text-red-700 mb-2">⚠️ Prazos Próximos ({prazos.length})</h2>
          <div className="space-y-1">
            {prazos.slice(0,5).map((p) => (
              <div key={p.id} className="flex items-center justify-between text-sm">
                <span className="font-medium text-red-800">{p.titulo}</span>
                <span className="text-red-600">{format(parseISO(p.data_inicio), "dd/MM HH:mm", { locale: ptBR })}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <select className="input max-w-40" value={filterTipo} onChange={(e) => setFilterTipo(e.target.value)}>
          <option value="">Todos os tipos</option>
          {TIPOS.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1)}</option>)}
        </select>
        <select className="input max-w-40" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">Todos status</option>
          {STATUS.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
        </select>
      </div>

      <div className="table-wrapper">
        <table className="table">
          <thead><tr>
            <th className="th">Título</th><th className="th">Tipo</th><th className="th">Data/Hora</th>
            <th className="th">Processo</th><th className="th">Local</th><th className="th">Status</th><th className="th">Ações</th>
          </tr></thead>
          <tbody>
            {loading ? <tr><td colSpan={7} className="td text-center text-gray-400 py-8">Carregando...</td></tr>
            : eventos.length === 0 ? <tr><td colSpan={7} className="td text-center text-gray-400 py-8">Nenhum evento encontrado</td></tr>
            : eventos.map((ev) => (
              <tr key={ev.id} className={`tr-hover ${rowClass(ev)}`}>
                <td className="td font-medium">{ev.titulo}</td>
                <td className="td"><span className={badgeEvento(ev.tipo)}>{ev.tipo}</span></td>
                <td className="td text-xs">{format(parseISO(ev.data_inicio), "dd/MM/yyyy HH:mm", { locale: ptBR })}</td>
                <td className="td text-xs">{ev.processo_numero || ev.processo || "—"}</td>
                <td className="td text-xs">{ev.local || "—"}</td>
                <td className="td"><span className={badgeStatus(ev.status)}>{ev.status}</span></td>
                <td className="td">
                  {ev.status === "pendente" && (
                    <button onClick={() => marcarRealizado(ev.id)} className="text-green-600 hover:text-green-800 text-xs font-medium">✓ Realizado</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">Novo Evento</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2"><label className="label">Título *</label><input className="input" required value={form.titulo} onChange={(e) => setForm({...form, titulo: e.target.value})} /></div>
                <div><label className="label">Tipo *</label><select className="input" value={form.tipo} onChange={(e) => setForm({...form, tipo: e.target.value})}>{TIPOS.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1)}</option>)}</select></div>
                <div><label className="label">Processo</label><select className="input" value={form.processo} onChange={(e) => setForm({...form, processo: e.target.value})}><option value="">Sem processo</option>{processos.map((p) => <option key={p.id} value={p.id}>{p.numero}</option>)}</select></div>
                <div><label className="label">Data/Hora início *</label><input className="input" type="datetime-local" required value={form.data_inicio} onChange={(e) => setForm({...form, data_inicio: e.target.value})} /></div>
                <div><label className="label">Data/Hora fim</label><input className="input" type="datetime-local" value={form.data_fim} onChange={(e) => setForm({...form, data_fim: e.target.value})} /></div>
                <div className="col-span-2"><label className="label">Local</label><input className="input" value={form.local} onChange={(e) => setForm({...form, local: e.target.value})} /></div>
                <div className="col-span-2"><label className="label">Descrição</label><textarea className="input" rows={2} value={form.descricao} onChange={(e) => setForm({...form, descricao: e.target.value})} /></div>
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary">Criar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
