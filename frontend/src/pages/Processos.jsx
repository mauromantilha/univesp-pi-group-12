import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import toast from "react-hot-toast";

const STATUS_LABELS = { em_andamento:"Em Andamento", suspenso:"Suspenso", finalizado:"Finalizado", arquivado:"Arquivado" };
const STATUS_BADGE = { em_andamento:"badge-blue", suspenso:"badge-yellow", finalizado:"badge-green", arquivado:"badge-gray" };
const POLO_LABELS = { ativo:"Ativo (autor)", passivo:"Passivo (réu)", terceiro:"Terceiro" };

export default function Processos() {
  const navigate = useNavigate();
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [clientes, setClientes] = useState([]);
  const [tipos, setTipos] = useState([]);
  const [varas, setVaras] = useState([]);
  const [form, setForm] = useState({ numero:"", cliente:"", tipo_processo:"", polo:"ativo", status:"em_andamento", parte_contraria:"", valor_causa:"", descricao:"" });

  const fetchProcessos = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (filterStatus) params.set("status", filterStatus);
    api.get(`/processos/?${params}`).then((r) => {
      setProcessos(r.data?.results || r.data || []);
    }).catch(() => toast.error("Erro ao carregar processos")).finally(() => setLoading(false));
  }, [search, filterStatus]);

  useEffect(() => { fetchProcessos(); }, [fetchProcessos]);

  useEffect(() => {
    if (showModal) {
      Promise.all([
        api.get("/clientes/").catch(() => ({ data: [] })),
        api.get("/tipos-processo/").catch(() => ({ data: [] })),
        api.get("/varas/").catch(() => ({ data: [] })),
      ]).then(([c, t, v]) => {
        setClientes(c.data?.results || c.data || []);
        setTipos(t.data?.results || t.data || []);
        setVaras(v.data?.results || v.data || []);
      });
    }
  }, [showModal]);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      await api.post("/processos/", form);
      toast.success("Processo criado!");
      setShowModal(false);
      setForm({ numero:"", cliente:"", tipo_processo:"", polo:"ativo", status:"em_andamento", parte_contraria:"", valor_causa:"", descricao:"" });
      fetchProcessos();
    } catch (err) {
      const msg = err.response?.data ? JSON.stringify(err.response.data).slice(0, 120) : "Erro ao criar processo";
      toast.error(msg);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">⚖️ Processos</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary gap-2">+ Novo Processo</button>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 flex-wrap">
        <input
          className="input max-w-xs"
          placeholder="Buscar número, cliente..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="input max-w-xs" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">Todos os status</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      {/* Tabela */}
      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th className="th">Número</th>
              <th className="th">Cliente</th>
              <th className="th">Tipo</th>
              <th className="th">Polo</th>
              <th className="th">Status</th>
              <th className="th">Valor</th>
              <th className="th">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="td text-center text-gray-400 py-8">Carregando...</td></tr>
            ) : processos.length === 0 ? (
              <tr><td colSpan={7} className="td text-center text-gray-400 py-8">Nenhum processo encontrado</td></tr>
            ) : processos.map((p) => (
              <tr key={p.id} className="tr-hover">
                <td className="td font-mono text-xs">{p.numero}</td>
                <td className="td font-medium">{p.cliente_nome || p.cliente}</td>
                <td className="td text-xs">{p.tipo_processo_nome || p.tipo_processo}</td>
                <td className="td text-xs">{POLO_LABELS[p.polo] || p.polo}</td>
                <td className="td"><span className={STATUS_BADGE[p.status] || "badge-gray"}>{STATUS_LABELS[p.status] || p.status}</span></td>
                <td className="td text-xs">{p.valor_causa ? `R$ ${Number(p.valor_causa).toLocaleString("pt-BR")}` : "—"}</td>
                <td className="td">
                  <button onClick={() => navigate(`/processos/${p.id}`)} className="text-primary-600 hover:text-primary-800 text-xs font-medium">
                    Ver detalhes →
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal Novo Processo */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold">Novo Processo</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Número *</label>
                  <input className="input" required value={form.numero} onChange={(e) => setForm({...form, numero: e.target.value})} />
                </div>
                <div>
                  <label className="label">Cliente *</label>
                  <select className="input" required value={form.cliente} onChange={(e) => setForm({...form, cliente: e.target.value})}>
                    <option value="">Selecione...</option>
                    {clientes.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Tipo de Processo *</label>
                  <select className="input" required value={form.tipo_processo} onChange={(e) => setForm({...form, tipo_processo: e.target.value})}>
                    <option value="">Selecione...</option>
                    {tipos.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Polo</label>
                  <select className="input" value={form.polo} onChange={(e) => setForm({...form, polo: e.target.value})}>
                    {Object.entries(POLO_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Parte Contrária</label>
                  <input className="input" value={form.parte_contraria} onChange={(e) => setForm({...form, parte_contraria: e.target.value})} />
                </div>
                <div>
                  <label className="label">Valor da Causa (R$)</label>
                  <input className="input" type="number" step="0.01" value={form.valor_causa} onChange={(e) => setForm({...form, valor_causa: e.target.value})} />
                </div>
              </div>
              <div>
                <label className="label">Descrição</label>
                <textarea className="input" rows={3} value={form.descricao} onChange={(e) => setForm({...form, descricao: e.target.value})} />
              </div>
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary">Criar Processo</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
