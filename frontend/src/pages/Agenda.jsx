import { useState, useEffect, useCallback } from "react";
import { format, parseISO, isPast, isToday, differenceInCalendarDays } from "date-fns";
import { ptBR } from "date-fns/locale";
import api from "../api/axios";
import toast from "react-hot-toast";

const TIPOS  = ["audiencia","prazo","reuniao","outro"];
const STATUS = ["pendente","concluido","cancelado"];

function badgeEvento(tipo) {
  const m = { audiencia:"badge-blue", prazo:"badge-red", reuniao:"badge-green", outro:"badge-gray" };
  return m[tipo] || "badge-gray";
}
function badgeStatus(s) {
  const m = { pendente:"badge-yellow", concluido:"badge-green", cancelado:"badge-red" };
  return m[s] || "badge-gray";
}

/** Build a JS-parseable ISO string from Django's separate date + hora fields */
function toISO(data, hora) {
  if (!data) return null;
  return hora ? `${data}T${hora}` : `${data}T00:00`;
}

function urgencyClass(data, hora) {
  const iso = toISO(data, hora);
  if (!iso) return "";
  const days = differenceInCalendarDays(parseISO(iso), new Date());
  if (days < 0) return "bg-red-100 border-red-400 text-red-800";
  if (days === 0) return "bg-red-50 border-red-400 text-red-700";
  if (days <= 3) return "bg-orange-50 border-orange-400 text-orange-700";
  return "bg-yellow-50 border-yellow-400 text-yellow-700";
}

function urgencyLabel(data, hora) {
  const iso = toISO(data, hora);
  if (!iso) return "—";
  const days = differenceInCalendarDays(parseISO(iso), new Date());
  if (days < 0) return `Vencido há ${Math.abs(days)} dia(s)`;
  if (days === 0) return "HOJE";
  if (days === 1) return "Amanhã";
  return `Em ${days} dias`;
}

function displayDataHora(data, hora) {
  const iso = toISO(data, hora);
  if (!iso) return "—";
  return hora
    ? format(parseISO(iso), "dd/MM/yyyy HH:mm", { locale: ptBR })
    : format(parseISO(iso), "dd/MM/yyyy", { locale: ptBR });
}

export default function Agenda() {
  const [eventos, setEventos]     = useState([]);
  const [prazos, setPrazos]       = useState([]);
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [filterTipo, setFilterTipo]     = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [showModal, setShowModal] = useState(false);
  // data_inicio is a datetime-local string e.g. "2026-02-24T14:30"; will be split before posting
  const [form, setForm] = useState({ titulo:"", tipo:"audiencia", data_inicio:"", processo:"", descricao:"" });

  const [processoInfoMap, setProcessoInfoMap] = useState({});

  const fetchAll = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filterTipo)   params.append("tipo", filterTipo);
    if (filterStatus) params.append("status", filterStatus);
    Promise.all([
      api.get(`/eventos/?${params}`),
      api.get("/eventos/prazos-proximos/"),
      api.get("/processos/?limit=200"),
    ]).then(([ev, pr, proc]) => {
      setEventos(ev.data?.results || ev.data || []);
      setPrazos(pr.data?.results || pr.data || []);
      const lista = proc.data?.results || proc.data || [];
      setProcessos(lista);
      const map = {};
      lista.forEach((p) => { map[p.id] = { numero: p.numero, tipo: p.tipo_nome || "" }; });
      setProcessoInfoMap(map);
    }).finally(() => setLoading(false));
  }, [filterTipo, filterStatus]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  function openModal() {
    setForm({ titulo:"", tipo:"audiencia", data_inicio:"", processo:"", descricao:"" });
    setShowModal(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      // Split datetime-local value into separate date and hora fields
      const [data, hora] = form.data_inicio ? form.data_inicio.split("T") : ["", ""];
      const payload = {
        titulo:    form.titulo,
        tipo:      form.tipo,
        data:      data,
        descricao: form.descricao,
      };
      if (hora)          payload.hora     = hora;
      if (form.processo) payload.processo = parseInt(form.processo);
      await api.post("/eventos/", payload);
      toast.success("Evento criado!");
      setShowModal(false);
      fetchAll();
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data).slice(0, 140) : "Erro ao salvar");
    }
  }

  async function marcarConcluido(id) {
    try {
      await api.patch(`/eventos/${id}/`, { status: "concluido" });
      toast.success("Marcado como concluído");
      fetchAll();
    } catch { toast.error("Erro ao atualizar"); }
  }

  function rowClass(ev) {
    if (ev.status === "concluido") return "opacity-50";
    if (!ev.data) return "";
    const iso = toISO(ev.data, ev.hora);
    if (ev.tipo === "prazo" && isPast(parseISO(iso)) && ev.status === "pendente") return "bg-red-50";
    if (isToday(parseISO(iso))) return "bg-yellow-50";
    return "";
  }

  const processoSelecionado = form.processo ? processoInfoMap[parseInt(form.processo)] : null;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">📅 Agenda</h1>
        <button onClick={openModal} className="btn-primary">+ Novo Evento</button>
      </div>

      {/* Painel de prazos próximos */}
      {prazos.length > 0 && (
        <div className="card border-l-4 border-red-500 bg-red-50">
          <h2 className="font-semibold text-red-700 mb-3">⚠️ Prazos Próximos ({prazos.length})</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {prazos.slice(0, 6).map((p) => (
              <div key={p.id} className={`flex items-center justify-between text-sm rounded-lg px-3 py-2 border ${urgencyClass(p.data, p.hora)}`}>
                <div>
                  <div className="font-semibold">{p.titulo}</div>
                  {p.processo_numero && <div className="text-xs opacity-75">Proc. {p.processo_numero}</div>}
                </div>
                <div className="text-right shrink-0 ml-3">
                  <div className="font-bold text-xs">{urgencyLabel(p.data, p.hora)}</div>
                  <div className="text-xs opacity-75">{displayDataHora(p.data, p.hora)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="flex gap-3">
        <select className="input max-w-40" value={filterTipo} onChange={(e) => setFilterTipo(e.target.value)}>
          <option value="">Todos os tipos</option>
          {TIPOS.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
        </select>
        <select className="input max-w-40" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">Todos status</option>
          {STATUS.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
        </select>
      </div>

      {/* Tabela */}
      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th className="th">Título</th>
              <th className="th">Tipo</th>
              <th className="th">Data/Hora</th>
              <th className="th">Processo</th>
              <th className="th">Status</th>
              <th className="th">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="td text-center text-gray-400 py-8">Carregando...</td></tr>
            ) : eventos.length === 0 ? (
              <tr><td colSpan={6} className="td text-center text-gray-400 py-8">Nenhum evento encontrado</td></tr>
            ) : eventos.map((ev) => (
              <tr key={ev.id} className={`tr-hover ${rowClass(ev)}`}>
                <td className="td font-medium">{ev.titulo}</td>
                <td className="td"><span className={badgeEvento(ev.tipo)}>{ev.tipo_display || ev.tipo}</span></td>
                <td className="td text-xs">{displayDataHora(ev.data, ev.hora)}</td>
                <td className="td text-xs">
                  {ev.processo_numero ? (
                    <span className="font-mono font-medium">{ev.processo_numero}</span>
                  ) : "—"}
                </td>
                <td className="td"><span className={badgeStatus(ev.status)}>{ev.status_display || ev.status}</span></td>
                <td className="td">
                  {ev.status === "pendente" && (
                    <button onClick={() => marcarConcluido(ev.id)} className="text-green-600 hover:text-green-800 text-xs font-medium">
                      ✓ Concluído
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal Novo Evento */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">Novo Evento / Prazo</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">

                {/* Título */}
                <div className="col-span-2">
                  <label className="label">Título *</label>
                  <input className="input" required value={form.titulo}
                    onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
                </div>

                {/* Tipo */}
                <div>
                  <label className="label">Tipo *</label>
                  <select className="input" value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
                    {TIPOS.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
                  </select>
                </div>

                {/* Processo vinculado */}
                <div>
                  <label className="label">Processo vinculado</label>
                  <select className="input" value={form.processo} onChange={(e) => setForm({ ...form, processo: e.target.value })}>
                    <option value="">— Sem processo —</option>
                    {processos.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.numero}{p.tipo_nome ? ` — ${p.tipo_nome}` : ""}
                      </option>
                    ))}
                  </select>
                  {processoSelecionado && (
                    <div className="mt-1 text-xs text-primary-700 font-medium bg-primary-50 rounded px-2 py-1">
                      📁 {processoSelecionado.numero}
                      {processoSelecionado.tipo && <span className="text-gray-500"> — {processoSelecionado.tipo}</span>}
                    </div>
                  )}
                </div>

                {/* Data/Hora */}
                <div className="col-span-2">
                  <label className="label">Data/Hora *</label>
                  <input className="input" type="datetime-local" required value={form.data_inicio}
                    onChange={(e) => setForm({ ...form, data_inicio: e.target.value })} />
                </div>

                {/* Descrição */}
                <div className="col-span-2">
                  <label className="label">Observações</label>
                  <textarea className="input" rows={2} value={form.descricao}
                    onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
                </div>
              </div>

              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary">Criar Evento</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

